"""MolmoAct2-DROID inference server — openpi websocket protocol.

This is a drop-in alternative to ``host_server_droid.py`` that speaks the
**openpi** policy-server wire protocol instead of the bespoke FastAPI ``/act``
HTTP endpoint. The point is so that the PolaRiS bench eval client
(``scripts/evaluation/evaluate_bench.py`` in the droid repo, which uses
``openpi_client.websocket_client_policy.WebsocketClientPolicy``) can talk to
MolmoAct2 with **no client changes** — exactly the same client used for the
pi0 / pi0.5 DROID checkpoints.

Wire protocol (matches openpi ``serve_policy.py`` /
``WebsocketPolicyServer``):

    * Transport: websocket, payloads serialized with msgpack + the openpi
      numpy extension (``msgpack_numpy`` below is a byte-for-byte copy of
      ``openpi_client.msgpack_numpy`` so the encodings are identical).
    * On connect the server sends one ``metadata`` frame.
    * Each request is an ``obs`` dict; the server replies with an ``action``
      dict. A ``server_timing`` field is added to every reply.

    request (obs), batched with a leading dim of 1 by the client:
        {
          "observation/exterior_image_1_left": uint8 (1, 224, 224, 3) RGB,
          "observation/wrist_image_left":      uint8 (1, 224, 224, 3) RGB,
          "observation/joint_position":        float (1, 7),
          "observation/gripper_position":      float (1, 1),
          "prompt":                            [str]  (list of length 1),
        }

    response (action):
        {
          "actions": float32 (1, N, 8),   # batch dim kept; client drops it
          "server_timing": {"infer_ms": float, ...},
        }

The action rows are ``[q1..q7, gripper]`` absolute joint positions, the same
8-D layout MolmoAct2-DROID emits natively (``norm_tag="franka_droid"``).

Model loading (snapshot-dir resolution, bf16 patches, processor / device
quirks) is reused verbatim from ``host_server_droid.Policy`` so the two
servers stay in lockstep — only the transport differs.

Run:

    uv run python examples/droid/host_server_droid_openpi.py --host 0.0.0.0 --port 8000

Then point the bench eval at it:

    uv run scripts/evaluation/evaluate_bench.py ... --remote-host <ip> --remote-port 8000
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import http
import logging
import time
import traceback

import msgpack
import numpy as np
import torch
import websockets.asyncio.server as ws_server
import websockets.frames

# Reuse the validated model-loading path (snapshot dir, bf16 patches, processor
# override, device-cast monkeypatch, coarse lock) from the FastAPI server so the
# two servers never drift. Importing it also runs ``json_numpy.patch()``, which
# is harmless here — we never touch stdlib json on the websocket path.
from host_server_droid import (  # noqa: E402  (sibling-module import)
    DEFAULT_NUM_STEPS,
    NORM_TAG,
    REPO_ID,
    Policy,
    warmup,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("molmoact2.server.openpi")


# --------------------------------------------------------------------------- #
# msgpack + numpy serialization — byte-for-byte copy of                       #
# openpi_client.msgpack_numpy so the encoding matches the client exactly.     #
# Copied (rather than imported) to avoid pulling in openpi-client, which pins  #
# numpy<2.0 and would conflict with this venv's numpy.                         #
# --------------------------------------------------------------------------- #
def _pack_array(obj):
    if (isinstance(obj, (np.ndarray, np.generic))) and obj.dtype.kind in ("V", "O", "c"):
        raise ValueError(f"Unsupported dtype: {obj.dtype}")

    if isinstance(obj, np.ndarray):
        return {
            b"__ndarray__": True,
            b"data": obj.tobytes(),
            b"dtype": obj.dtype.str,
            b"shape": obj.shape,
        }

    if isinstance(obj, np.generic):
        return {
            b"__npgeneric__": True,
            b"data": obj.item(),
            b"dtype": obj.dtype.str,
        }

    return obj


def _unpack_array(obj):
    if b"__ndarray__" in obj:
        return np.ndarray(buffer=obj[b"data"], dtype=np.dtype(obj[b"dtype"]), shape=obj[b"shape"])

    if b"__npgeneric__" in obj:
        return np.dtype(obj[b"dtype"]).type(obj[b"data"])

    return obj


_Packer = functools.partial(msgpack.Packer, default=_pack_array)
_unpackb = functools.partial(msgpack.unpackb, object_hook=_unpack_array)


# --------------------------------------------------------------------------- #
# Bridge: openpi obs dict  ->  MolmoAct2 predict_action  ->  openpi action dict #
# --------------------------------------------------------------------------- #
def _drop_batch(arr: np.ndarray, ndim_unbatched: int) -> np.ndarray:
    """The bench client adds a leading batch dim of 1 to every field. Strip it
    if present so we hand MolmoAct2 unbatched inputs. Tolerates already-unbatched
    inputs too."""
    arr = np.asarray(arr)
    if arr.ndim == ndim_unbatched + 1 and arr.shape[0] == 1:
        return arr[0]
    return arr


def _scalar_prompt(prompt) -> str:
    # Client sends prompt as a length-1 list; also tolerate raw str / bytes.
    if isinstance(prompt, (list, tuple)):
        prompt = prompt[0] if prompt else ""
    if isinstance(prompt, bytes):
        prompt = prompt.decode("utf-8")
    return str(prompt)


class MolmoActDroidPolicy:
    """Adapts ``host_server_droid.Policy`` to the openpi ``infer(obs) -> dict``
    interface."""

    def __init__(self, policy: Policy, num_steps: int = DEFAULT_NUM_STEPS) -> None:
        self._policy = policy
        self._num_steps = num_steps
        self.metadata = {
            "policy": "molmoact2-droid",
            "repo_id": REPO_ID,
            "norm_tag": NORM_TAG,
            "action_dim": 8,
            "num_steps": num_steps,
        }

    def infer(self, obs: dict) -> dict:
        external = _drop_batch(obs["observation/exterior_image_1_left"], 3)  # (H, W, 3)
        wrist = _drop_batch(obs["observation/wrist_image_left"], 3)  # (H, W, 3)
        joint = _drop_batch(obs["observation/joint_position"], 1).reshape(-1)  # (7,)
        gripper = _drop_batch(obs["observation/gripper_position"], 1).reshape(-1)  # (1,)
        instruction = _scalar_prompt(obs.get("prompt", ""))

        # MolmoAct2-DROID expects an 8-D state = [q1..q7, gripper].
        state = np.concatenate([joint, gripper]).astype(np.float32)
        if state.shape != (8,):
            raise ValueError(
                f"expected 8-D state from joint(7)+gripper(1), got {state.shape} "
                f"(joint={joint.shape}, gripper={gripper.shape})"
            )

        actions = self._policy.predict(
            external_cam=np.asarray(external),
            wrist_cam=np.asarray(wrist),
            instruction=instruction,
            state=state,
            num_steps=self._num_steps,
            enable_cuda_graph=self._policy.default_cuda_graph,
        )  # (N, 8)
        actions = np.asarray(actions, dtype=np.float32)
        if actions.ndim != 2 or actions.shape[1] != 8:
            raise ValueError(f"expected (N, 8) actions, got {actions.shape}")

        # Keep the leading batch dim the client expects (it does actions[0]).
        return {"actions": actions[None]}


# --------------------------------------------------------------------------- #
# Websocket server — mirrors openpi.serving.websocket_policy_server.            #
# --------------------------------------------------------------------------- #
class WebsocketPolicyServer:
    def __init__(self, policy: MolmoActDroidPolicy, host: str, port: int) -> None:
        self._policy = policy
        self._host = host
        self._port = port
        self._metadata = policy.metadata

    def serve_forever(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        async with ws_server.serve(
            self._handler,
            self._host,
            self._port,
            compression=None,
            max_size=None,
            process_request=_health_check,
        ) as server:
            log.info("Listening on ws://%s:%d", self._host, self._port)
            await server.serve_forever()

    async def _handler(self, websocket: ws_server.ServerConnection) -> None:
        log.info("Connection from %s opened", websocket.remote_address)
        packer = _Packer()
        await websocket.send(packer.pack(self._metadata))

        prev_total_time = None
        while True:
            try:
                start_time = time.monotonic()
                obs = _unpackb(await websocket.recv())

                infer_time = time.monotonic()
                # Inference is blocking (and serialized by Policy's lock); run it
                # off the event loop so the websocket stays responsive.
                action = await asyncio.to_thread(self._policy.infer, obs)
                infer_time = time.monotonic() - infer_time

                action["server_timing"] = {"infer_ms": infer_time * 1000}
                if prev_total_time is not None:
                    action["server_timing"]["prev_total_ms"] = prev_total_time * 1000

                await websocket.send(packer.pack(action))
                prev_total_time = time.monotonic() - start_time
            except websockets.ConnectionClosed:
                log.info("Connection from %s closed", websocket.remote_address)
                break
            except Exception:
                log.exception("inference failed")
                await websocket.send(traceback.format_exc())
                await websocket.close(
                    code=websockets.frames.CloseCode.INTERNAL_ERROR,
                    reason="Internal server error. Traceback included in previous frame.",
                )
                raise


def _health_check(connection: ws_server.ServerConnection, request: ws_server.Request):
    if request.path == "/healthz":
        return connection.respond(http.HTTPStatus.OK, "OK\n")
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="MolmoAct2-DROID inference server (openpi websocket protocol)"
    )
    p.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)")
    p.add_argument("--port", type=int, default=8000, help="bind port (default: 8000)")
    p.add_argument("--repo-id", default=REPO_ID, help=f"HF repo id (default: {REPO_ID})")
    p.add_argument("--device", default="cuda:0", help="torch device (default: cuda:0)")
    p.add_argument(
        "--dtype",
        default="bfloat16",
        choices=["bfloat16", "float16", "float32"],
        help="model dtype (default: bfloat16)",
    )
    p.add_argument(
        "--num-steps",
        type=int,
        default=DEFAULT_NUM_STEPS,
        help=f"flow-matching integration steps (default: {DEFAULT_NUM_STEPS})",
    )
    p.add_argument("--no-warmup", action="store_true", help="skip warmup pass")
    p.add_argument(
        "--cuda-graph",
        action="store_true",
        help="enable CUDA graph capture for action expert (faster but ~2 GB more VRAM)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    dtype = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[args.dtype]

    import os

    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

    policy = Policy(
        repo_id=args.repo_id,
        device=args.device,
        dtype=dtype,
        enable_cuda_graph=args.cuda_graph,
    )
    if not args.no_warmup:
        warmup(policy)

    bridge = MolmoActDroidPolicy(policy, num_steps=args.num_steps)
    server = WebsocketPolicyServer(bridge, host=args.host, port=args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
