## Qt GUI for Stable diffusion
--------
Built from the ground up alongside [sd-inference-server](https://github.com/stromtroopertk421/sd-inference-server), the backend for this GUI.
![example](https://github.com/arenasys/qDiffusion/raw/master/source/screenshot.png)
\*new\* Discord: [Arena Systems](https://discord.gg/WdjKqUGefU).

## Getting started
### Runtime requirements
- Baseline runtime: **Python 3.14**.
- First-run launch scripts (`qDiffusion.exe`, `source/start.sh`, `source/start-mac.sh`) automatically provision a bundled Python 3.14 runtime when needed.
- Disk guidance remains the same: `Remote` installs are lighter (~500MB), while local accelerator installs (`NVIDIA`/`AMD`) typically require several GB for inference dependencies and model tooling.

#### Supported OS and accelerator combinations
| OS | Remote | NVIDIA (CUDA) | AMD |
| --- | --- | --- | --- |
| Windows 10/11 | ✅ Supported | ✅ Supported | ✅ Supported via DirectML (functional, but slower than Linux ROCm) |
| Linux (x86_64) | ✅ Supported | ✅ Supported | ✅ Supported via ROCm |
| macOS (Apple Silicon / Intel) | ✅ Supported | ⚠️ Not supported | ⚠️ Local AMD path not supported |

Temporary exceptions:
- Cloud notebook providers may still expose system Python versions that lag behind 3.14. qDiffusion remote notebooks should be treated as **Python 3.14 baseline workflows**, but provider-managed kernels can remain an external constraint until each platform fully rolls forward.
- Some packages in the torch / Qt stack may temporarily publish wheels later than pure-Python packages for brand-new Python runtimes.

### Install
1. [Download](https://github.com/arenasys/qDiffusion/archive/refs/heads/master.zip) this repo as a zip and extract it.
2. Run `qDiffusion.exe` (or `bash ./source/start.sh` on Linux, `sh ./source/start-mac.sh` on Mac).
	- First-time setup provisions the bundled Python 3.14 runtime and PyQt before launch.
	- AMD Ubuntu users need to follow: [Install ROCm](https://github.com/arenasys/qDiffusion/wiki/Install#ubuntu-22).
3. Select a mode. `Remote`, `Nvidia` and `AMD` are available.
	- `Remote` needs `~500MB` of space, `NVIDIA`/`AMD` need `~5-10GB`.
	- Choose `Remote` if you only want to generate using cloud/server instances.
	- For local generation choose `NVIDIA` or `AMD`, they also have the capabilities of `Remote`.
	- `AMD` on Windows uses DirectML so is much slower than on Linux.
4. Press Install. Requirements will be downloaded.
	- Output is displayed on screen, fatal errors are written to `crash.log`.
5. Done. NOTE: Update using `File->Update` or `Settings->Program->Update`.

Information is available on the [Wiki](https://github.com/arenasys/qDiffusion/wiki/Guide).

### Troubleshooting: wheel availability (torch / Qt)
If installation fails with errors such as `No matching distribution found`, `Could not find a version that satisfies the requirement`, or `Failed building wheel`, use the checklist below:

1. Confirm the runtime is the bundled Python 3.14 environment (not a different system Python).
2. Retry after clearing partially downloaded artifacts from the local install folder.
3. For local GPU modes, verify you selected the correct backend (`NVIDIA` vs `AMD`) and have the required driver/runtime stack installed.
4. If `torch`, `torchvision`, or Qt/PyQt wheels are temporarily unavailable for your exact platform, switch to `Remote` mode while waiting for wheel publication.
5. On Linux AMD, ensure ROCm prerequisites from the wiki are fully applied before re-running install.

When reporting issues, include:
- OS version and architecture
- Selected mode (`Remote` / `NVIDIA` / `AMD`)
- The exact package name that failed
- `crash.log` excerpt from the failure section

### Remote
Notebooks for running a remote instance are available: [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb), [Kaggle](https://www.kaggle.com/code/arenasys/qdiffusion), [SageMaker](https://studiolab.sagemaker.aws/import/github/arenasys/qDiffusion/blob/master/remote_sagemaker.ipynb)

Remote/notebook guidance follows the same Python 3.14 baseline. If a hosted service has not yet rolled out 3.14 wheels for a dependency, that provider lag is considered a temporary exception; rerun later or use another backend/runtime option.

0. [Install](#install) qDiffusion, this runs locally on your machine and connects to the backend server.
	- If using Mobile then skip this step.
1. Open the [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb) notebook. Requires a Google account.
2. Press the play button in the top left. Colab may take some time to configure a machine for you.
3. Accept or reject the Google Drive permission popup.
	- Accepting will mean models are saved/loaded from `qDiffusion/models` on your drive.
	- Rejecting will mean models are local, you will need to download them again next time.
4. Wait for the requirements to be downloaded and the server to start (scroll down).
5. Click the `DESKTOP` link to start qDiffusion and/or connect.
   	- Alternatively copy the Endpoint and Password to qDiffusion under `Settings->Remote`, press Connect.
6. Done. See [Downloads](https://github.com/arenasys/qDiffusion/wiki/Guide#downloading) for how to get models onto the instance.
	- Remaking the instance is done via `Runtime->Disconnect and delete runtime`, then close the tab and start from Step 1.
	- HTTP 530 means the cloudflare tunnel is not working. Wait for an update, or check [Here](https://www.cloudflarestatus.com/).
	- Runtime disconnects due to "disallowed code" can happen occasionally, often when merging. For now these don't appear to be targeted at qDiffusion specifically.

### Mobile
[qDiffusion Web](https://github.com/arenasys/arenasys.github.io) is available for mobile users. Features are limited compared to the full GUI (txt2img only).

### Overview
- Stable diffusion 1.x, 2.x (including v-prediction), XL (only Base)
- Txt2Img, Img2Img, Inpainting, HR Fix and Upscaling modes
- Prompt and network weighting and scheduling
- Hypernetworks
- LoRAs (including LoCon)
- Textual inversion Embeddings
- Model pruning and conversion
- Subprompts via Composable Diffusion
- Live preview modes
- Optimized attention
- Minimal VRAM mode
- Device selection
- ControlNet
- Merging
- ~~LoRA Training~~ (working on it!)
