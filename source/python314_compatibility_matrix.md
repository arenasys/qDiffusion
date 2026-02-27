# Python 3.14 compatibility matrix (GUI + inference requirements)

> Scope: every pinned package previously listed in `source/requirements_gui.txt` and `source/requirements_inference.txt`.
>
> Wheel status legend:
> - **cp314/py3 wheel required**: package should resolve without local compile on Python 3.14.
> - **pure-python**: uses `py3-none-any` wheels; interpreter minor version is typically not a wheel blocker.
>
> Note: this matrix is intended to drive lock updates for Python 3.14 migration and records the selected version floor per package.

| Package | Previous pin | Python 3.14 wheel status at previous pin | Selected floor for Python 3.14 | Action |
|---|---:|---|---:|---|
| Pillow | `>=9.5.0` | old floor not lock-safe | `11.0.0` | pin for deterministic lock |
| websockets | `11.0.3` | pure-python | `12.0` | bump for modern Python floor |
| bson | `0.5.10` | pure-python | `0.5.10` | unchanged |
| Send2Trash | `1.8.2` | pure-python | `1.8.3` | minor bump |
| PyOpenGL | `3.1.7` | pure-python | `3.1.9` | minor bump |
| PyQt5 | `5.15.7` | fragile for new interpreters | `PySide6==6.8.1` | migrated to active Qt line used by this codebase |
| cryptography | `40.0.2` | compiled wheel line too old | `44.0.1` | bump to current binary line |
| numpy | `1.24.3` | compiled wheel line too old | `2.2.2` | bump to Python 3.14-capable line |
| pygit2 | `1.12.1` | compiled wheel line too old | `1.17.0` | bump |
| packaging | _(transitive)_ | pure-python | `24.2` | promote to explicit runtime dependency for installer requirement parsing |
| diffusers | `0.27.2` | pure-python, dependency floor drift | `0.35.1` | bump |
| einops | `0.6.1` | pure-python | `0.8.1` | bump |
| k_diffusion | `0.0.15` | pure-python but old deps | `0.1.1.post1` | bump |
| lark | `1.1.5` | pure-python | `1.2.2` | bump |
| safetensors | `0.3.1` | compiled wheel line too old | `0.5.3` | bump |
| tqdm | `4.65.0` | pure-python | `4.67.1` | bump |
| transformers | `4.36.2` | pure-python, transitive floor drift | `4.49.0` | bump + align HF stack |
| spandrel | `0.4.1` | pure-python | `0.4.1` | unchanged |
| opencv-python-headless | `4.7.0.72` | compiled wheel line too old | `4.12.0.88` | bump |
| timm | `0.9.2` | pure-python | `1.0.11` | bump |
| tomesd | `0.1.3` | pure-python | `0.1.3` | unchanged |
| pycloudflared | `0.2.0` | pure-python | `0.2.0` | unchanged |
| segment-anything | `1.0` | pure-python | `1.0` | unchanged |
| geffnet | `1.0.2` | pure-python | `1.0.2` | unchanged |
| toml | `0.10.2` | pure-python | `0.10.2` | unchanged |
| voluptuous | `0.13.1` | pure-python | `0.15.2` | bump |
| accelerate | `0.27.2` | pure-python, transitive floor drift | `1.2.1` | bump + align HF stack |
| lycoris-lora | `2.3.0.dev4` | pure-python | `2.3.0.dev4` | unchanged (project-specific) |
| ultralytics | `8.2.3` | pure-python, transitive floor drift | `8.3.40` | bump |
| huggingface_hub | `0.25.1` | pure-python | `0.29.2` | bump + align HF stack |

## Platform-specific accelerator pins

- `torch==2.6.0 ; platform_system != "Windows"`
- `torchvision==0.21.0 ; platform_system != "Windows"`
- `torch-directml==0.2.5.dev240914 ; platform_system == "Windows"`

These constraints are kept explicit in `source/requirements_inference.txt` to avoid mixing CUDA/CPU and DirectML channels in a single unconstrained solver run.


## sd-inference-server mapping criteria

- qDiffusion installer resolves inference dependencies from `source/sd-inference-server` first (if present), before using `source/requirements_inference.txt` as fallback.
- Fallback pins in `source/requirements_inference.txt` are kept aligned to the upgraded inference stack and should only be used when the sub-repo is unavailable.
- This preserves compatibility with your fork-specific `sd-inference-server` requirements while keeping standalone installs deterministic.
