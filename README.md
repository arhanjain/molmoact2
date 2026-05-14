<div align="center">
  <img src="assets/MolmoAct2.svg" alt="MolmoAct2 Logo" width="800" style="margin-left:'auto' margin-right:'auto' display:'block'"/>
  <br>
  <br>
  <h1>MolmoAct2: Action Reasoning Models for Real-world Deployment</h1>
</div>

<p align="center">
  <a href="https://github.com/allenai/molmoact2/blob/main/LICENSE">
    <img alt="GitHub License" src="https://img.shields.io/github/license/allenai/molmoact2">
  </a>
  <a href="https://allenai.org/blog/molmoact2">
    <img alt="Blog Post" src="https://img.shields.io/badge/Blog-Post-F0529C">
  </a>
  <a href="https://arxiv.org/abs/2605.02881">
    <img alt="Paper URL" src="https://img.shields.io/badge/arXiv-2605.02881-red?logo=arxiv">
  </a>
  <a href="https://huggingface.co/collections/allenai/molmoact2-models-69f81e05242e2499606b1be6">
    <img alt="Base Models" src="https://img.shields.io/badge/HF-Base%20Models-yellow?logo=huggingface">
  </a>
  <a href="https://huggingface.co/collections/allenai/molmoact2-finetuned-models-69f81e23d5a7b34fde34f2ce">
    <img alt="Finetuned Models" src="https://img.shields.io/badge/HF-Finetuned%20Models-yellow?logo=huggingface">
  </a>
  <a href="https://huggingface.co/collections/allenai/molmoact2-bimanualyam-dataset-69f81e17b140ec34f430a35e">
    <img alt="MolmoAct2-BimanualYAM Dataset" src="https://img.shields.io/badge/HF-MolmoAct2--BimanualYAM%20Dataset-yellow?logo=huggingface">
  </a>
  <a href="https://huggingface.co/collections/allenai/molmoact2-datasets-69f81e316ec3daafe3f9555c">
    <img alt="Robotics Datasets" src="https://img.shields.io/badge/HF-Robotics%20Datasets-yellow?logo=huggingface">
  </a>
  <a href="https://huggingface.co/collections/allenai/molmo2-er-datasets-69f8d605d92d46a5fc24ced2">
    <img alt="ER Datasets" src="https://img.shields.io/badge/HF-ER%20Datasets-yellow?logo=huggingface">
  </a>
</p>

MolmoAct2 is Ai2's open family of action reasoning models for robot control and real-world deployment. It builds on the Molmo2-ER embodied-reasoning vision-language backbone, adds robot state and action modeling, and connects the VLM to a flow-matching continuous action expert for closed-loop manipulation. The release includes base checkpoints for continued training, fine-tuned robot policies for evaluation and deployment, and the datasets used to build MolmoAct2 and Molmo2-ER.

---
### Updates
- **[2026/05/14]** 🔥 We have released MolmoAct2 lerobot workflow for fine-tuning and inference. [**Check it out**](https://github.com/allenai/lerobot/tree/molmoact2-policy). 
- **[2025/05/06]** 🔥 Detail implementation and setup for Franka, SO-100/101, and bimanual YAM have been released at  [**2 Real-world Deployment**](#2-real-world-deployment).
- **[2026/05/05] 🔥 [MolmoAct2]([https://huggingface.co/collections/allenai/molmoact-689697591a3936fba38174d7](https://allenai.org/blog/molmoact2))** has been released!


## 1 Models

### Base Models

We provide base checkpoints at every training stage for continued MolmoAct2 training and robot fine-tuning. These are foundation checkpoints rather than one-size-fits-all deployment policies.

| Model | Use Case | Description | Checkpoint Path |
| --- | --- | --- | --- |
| MolmoAct2 | Fine-tuning | Post-trained MolmoAct2 model with a continuous flow-matching action expert. Use as the default foundation checkpoint for adapting to a target robot embodiment or benchmark. | https://huggingface.co/allenai/MolmoAct2 |
| MolmoAct2-Think | Fine-tuning | MolmoAct2 foundation checkpoint with depth-token reasoning. Use when downstream policies should reason over compact depth predictions before acting. | https://huggingface.co/allenai/MolmoAct2-Think |
| MolmoAct2-Pretrain | Post-training | Pre-trained discrete autoregressive VLA backbone before the continuous action expert is attached. Intended for continuing MolmoAct2 training stages, not direct continuous-control inference. | https://huggingface.co/allenai/MolmoAct2-Pretrain |
| Molmo2-ER | Pre-training | Embodied-reasoning VLM backbone used as the starting point for MolmoAct2 action models. | https://huggingface.co/allenai/Molmo2-ER |

### Finetuned Models

We also provide fine-tuned checkpoints for common robot platforms and benchmarks. These models are intended to run directly in their target setting, or to serve as a stronger starting point for closely related robots. As with any robot policy, performance depends on hardware, cameras, calibration, action conventions, and language/task distribution.

| Model | Use Case | Description | Checkpoint Path |
| --- | --- | --- | --- |
| MolmoAct2-DROID | Inference / Fine-tuning | MolmoAct2 fine-tuned on the filtered DROID Franka mixture with absolute joint-pose control. Intended for DROID-style policy inference or further fine-tuning. | https://huggingface.co/allenai/MolmoAct2-DROID |
| MolmoAct2-BimanualYAM | Inference / Fine-tuning | MolmoAct2 fine-tuned on the bimanual YAM mixture with absolute joint-pose control and annotated language instructions. | https://huggingface.co/allenai/MolmoAct2-BimanualYAM |
| MolmoAct2-SO100_101 | Inference / Fine-tuning | MolmoAct2 fine-tuned on SO-100/SO-101 datasets with absolute joint-pose control and annotated language instructions. | https://huggingface.co/allenai/MolmoAct2-SO100_101 |
| MolmoAct2-LIBERO | Inference / Fine-tuning | MolmoAct2 fine-tuned on the full LIBERO training mixture, combining Spatial, Object, Goal, and Long suites. | https://huggingface.co/allenai/MolmoAct2-LIBERO |
| MolmoAct2-Think-LIBERO | Inference / Fine-tuning | MolmoAct2-Think fine-tuned on LIBERO with depth-and-action examples and adaptive depth reasoning. | https://huggingface.co/allenai/MolmoAct2-Think-LIBERO |

## Datasets

| Data | Description | Dataset Path |
| --- | --- | --- |
| MolmoAct2-BimanualYAM Dataset | Collection of bimanual YAM datasets and related resources used for MolmoAct2 bimanual training and evaluation. | https://huggingface.co/collections/allenai/molmoact2-bimanualyam-dataset-69f81e17b140ec34f430a35e |
| MolmoAct2 Robotics Datasets | Robotics datasets for MolmoAct2 training and fine-tuning, including SO-100/SO-101, DROID, MolmoAct Dataset, BC-Z, Bridge, and RT-1. | https://huggingface.co/collections/allenai/molmoact2-datasets-69f81e316ec3daafe3f9555c |
| Molmo2-ER Datasets | Embodied reasoning datasets used for Molmo2-ER and MolmoAct2 backbone training, including spatial, 3D, robotics, and visual reasoning data. | https://huggingface.co/collections/allenai/molmo2-er-datasets-69f8d605d92d46a5fc24ced2 |

Note that all of the robotics datasets for pre-training and post-training are in LeRobot v3.0 format, paired with extra language annotations.

## LeRobot Integration

MolmoAct2 is integrated into LeRobot as a policy implementation, so users can train, evaluate, and deploy MolmoAct2 with standard LeRobot datasets and workflows. This repository includes the LeRobot integration as a Git submodule at `lerobot/`, pinned to the [`allenai/lerobot` `molmoact2-policy` branch](https://github.com/allenai/lerobot/tree/molmoact2-policy).

For training, although all of our experiments start from the base checkpoint [`allenai/MolmoAct2`](https://huggingface.co/allenai/MolmoAct2), we recommend starting from the fine-tuned checkpoints listed in the [Finetuned Models](#finetuned-models) section above if your embodiment is similar to [Bimanual YAM](https://huggingface.co/allenai/MolmoAct2-BimanualYAM), [DROID Franka](https://huggingface.co/allenai/MolmoAct2-DROID), or [SO-100/SO-101](https://huggingface.co/allenai/MolmoAct2-SO100_101), as they can provide better initialization and downstream performance. For generic use, use the base checkpoint.

After cloning this repository, initialize the submodule from the repo root:

```bash
git submodule update --init --recursive
cd lerobot
```

For training, evaluation, and deployment instructions, see the MolmoAct2 LeRobot documentation at [`docs/source/molmoact2.mdx`](https://github.com/allenai/lerobot/blob/molmoact2-policy/docs/source/molmoact2.mdx). To reproduce the original LIBERO benchmark results exactly with the v0.5.1 evaluation stack, use the pinned inference branch [`allenai/lerobot:molmoact2-hf-inference`](https://github.com/allenai/lerobot/tree/molmoact2-hf-inference).

## 2 Real-world Deployment

MolmoAct2 supports out-of-the-box deployment on three robot embodiments:

- **SO-100**
- **Bimanual YAMs**
- **Franka DROID setup**

### SO-100 Setup

For the best performance, we recommend using an **SO-100 with the standard wrist configuration** and a **third-person camera**.

### Bimanual YAM Setup

For the best performance, please build your Bimanual YAM setup following the reference design below:

![Bimanual YAM setup](assets/m.png)

All required components can be purchased using this [Bimanual YAM parts list](https://docs.google.com/spreadsheets/d/10bg4XJoeIqnuOBLpUlkhJV6QEYn_oK5IZVm5C7_kdbo/edit?usp=sharing).

Implementation code for setting up, data collection, and inference for Bimanual YAM is [here](https://github.com/williamtsai726/YAM)

### Franka Setup

For the Franka setup, we recommend following the official [DROID implementation](https://github.com/droid-dataset/droid) for best results.

## 3 Coming Soon

Full code for training, fine-tuning, deployment, evaluation, and more details are coming soon.

## 4 License

This model is licensed under Apache 2.0. It is intended for research and educational use in accordance with Ai2's [Responsible Use Guidelines](https://allenai.org/responsible-use).

## 5 Model and Hardware Safety
MolmoAct2 generate robot actions from visual observations and language instructions, but their behavior may vary across embodiments, environments, and hardware configurations. Users should carefully validate model outputs before deployment, especially when operating physical robots or other actuated systems. Where possible, actions should be monitored through interpretable intermediate outputs (adaptive depth map), simulation rollouts, action limits, or other safety checks before execution on hardware. The model’s action space should be bounded by the training data, robot controller limits, and task-specific safety constraints, including limits on speed, workspace, torque, and contact force. Users should follow the hardware manufacturer’s safety guidelines, use appropriate emergency-stop mechanisms, and operate the system only in a safely configured environment with human supervision.

## 6 Contacts

For questions, collaborations, or support, please contact with:
```
{hqfang,duanj1}@cs.washington.edu 
```
Found a bug or have a feature request? Please open a GitHub issue.

## 7 Citation

```bibtex
@misc{fang2026molmoact2actionreasoningmodels,
      title={MolmoAct2: Action Reasoning Models for Real-world Deployment}, 
      author={Haoquan Fang and Jiafei Duan and Donovan Clay and Sam Wang and Shuo Liu and Weikai Huang and Xiang Fan and Wei-Chuan Tsai and Shirui Chen and Yi Ru Wang and Shanli Xing and Jaemin Cho and Jae Sung Park and Ainaz Eftekhar and Peter Sushko and Karen Farley and Angad Wadhwa and Cole Harrison and Winson Han and Ying-Chun Lee and Eli VanderBilt and Rose Hendrix and Suveen Ellawela and Lucas Ngoo and Joyce Chai and Zhongzheng Ren and Ali Farhadi and Dieter Fox and Ranjay Krishna},
      year={2026},
      eprint={2605.02881},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2605.02881}, 
}
```
