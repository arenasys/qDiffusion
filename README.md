## Qt GUI for Stable diffusion
--------
Built from the ground up alongside [sd-inference-server](https://github.com/arenasys/sd-inference-server), the backend for this GUI.
![example](https://github.com/arenasys/qDiffusion/raw/master/screenshot.png)
## Getting started
### Install
1. [Download](https://github.com/arenasys/qDiffusion/archive/refs/heads/master.zip) this repo as a zip and extract it.
2. Run `qDiffusion.exe`, `start_win.bat` or `start_linux.sh`.
	- First time users will need to wait for Python and PyQt5 to be downloaded.
3. Select a mode. `Remote`, `Nvidia` and `AMD` are available.
	- `Remote` needs `~500MB` of space, `NVIDIA`/`AMD` need `~5-10GB`.
	- Choose `Remote` if you only want to generate using cloud/server instances.
	- For local generation choose `NVIDIA` or `AMD`, they also have the capabilities of `Remote`.
	- `AMD` on Windows uses DirectML so is much slower than on Linux.
4. Press Install. Requirements will be downloaded.
	- Output is displayed on screen, fatal errors are written to `crash.log`.
5. Done. NOTE: Update using `File->Update` or `Settings->Program->Update`.

### Remote
Notebooks for running a remote instance are available: [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb), [Kaggle](https://www.kaggle.com/code/arenasys/qdiffusion)
1. Open the [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb) notebook. Requires a Google account.
2. Press the play button in the top left. Colab may take some time to configure a machine for you.
3. Accept or reject the Google Drive permission popup.
	- Accepting will mean models are saved/loaded from `qDiffusion/models` on your drive.
	- Rejecting will mean models are local, you will need to download them again next time.
4. Wait for the requirements to be downloaded and the server to start.
5. Copy the Endpoint and Password to qDiffusion under `Settings->Remote`, press Connect.
6. Done. See [Downloads](Downloads) for how to get models onto the instance.

## Details
### Startup
qDiffusion is capable of installing from scratch, even without python installed. This is an automatic process:
1. `qDiffusion.exe`. Ensures python is available, downloading if needed. Then runs `launch.py`
2. `launch.py`. Ensures a venv is active and PyQT5 is installed. Then imports `main.py`
	- Qt cannot be loaded from paths containing unicode characters (`ユニコード`, etc)
	- The venv is installed at the base of the drive if this is detected (`C:\qDiffusion`)
3. `main.py`. Bootstraps the GUI:
	1. Starts the GUI in a minimal state. The splash screen is shown while QML sources are compiled.
	2. Ensures the requirements are met for the chosen mode (`Nvidia`, `AMD`, or `Remote`).
		- Install screen prompts the user to install missing requirements (`requirements_*.txt`)
		- Skipped if no venv is active. Forced to show if `config.json` contains `'show': true`
		- Versions are not enforced, so different versions of torch/diffusers/xformers can be used.
	3. Starts the full GUI `Main.qml`, `gui.py`. Tabs are initialized, loaded and connected to the GUI.

Run `python source\main.py` directly to prevent qDiffusion from messing with venv's or the environment.

### Updating
Updating with the GUI is equivilent to `git fetch; git reset -hard HEAD`, so **ALL CHANGES MADE TO THE CODE WILL BE LOST**. Manually updating can be done by `git pull; cd source/sd-inference-server; git pull`.

### Backend
The backend is started once the GUI is ready, and can be reloaded via `File->Reload`.

In local inference mode (`Nvidia or AMD`) the inference repo is cloned into `source\sd-inference-server`, then a child process called `LocalInference` is created to run the server (`local.py`). Communication happens directly between the GUI and inference processes, so the server is not exposed on any network interface. A separate process is required since python will freeze for multiple seconds when importing large libraries (`torch`, `diffusers`, etc).

In remote mode (`remote.py`) the inference repo is not cloned and there is no child process, instead a thread will run a websocket client and relay requests/responses to the remote websocket server (`server.py`), all messages are BSON encoded and encrypted for authentication (before TLS). Any websocket aware HTTP proxy can route these connections. The server is mostly stateless, each request is fully independent, and all responses are relayed back to the client without writing to the disk (except for some error logging). The exception is the models, which are managed between requests to reduce overhead and VRAM usage.

### Models
The primary model format is `safetensors`. Pickled models are also supported but not recommended: `ckpt`, `pt`, `pth`, `bin`, etc. Diffusers folders are also supported. The model structure is flexible, supporting both the A1111 folder layout and qDiffusions own layout:
- Checkpoint: `SD`, `Stable-diffusion`, `VAE`
- Upscaler/Super resolution: `SR`, `ESRGAN`, `RealESRGAN`
- Embedding/Textual Inversion: `TI`, `embeddings`, `../embeddings`
- LoRA: `LoRA`
- Hypernet: `HN`, `hypernetworks`
- ControlNet: `CN`, `ControlNet`

VAE's need `.vae.` in their filename to be recognized as external: `PerfectColors.vae.safetensors`. Embeddings in a subfolder with "negative" in the folder name will be considered negative embeddings. Subfolders/models starting with `_` will be ignored. Pruning is available by right clicking the model in the models tab, Hypernetworks cannot be pruned. The currently active UNET, VAE, CLIP and LoRA's (if network mode is `Static`) can be combined into a model with `Edit->Build model`.

### Downloading
Remote instances can download models from URL's or receive models uploaded by the client (`Settings->Remote`). Some sources have special support:
- `Civit.ai`: Right click the models download button and copy the link.
	- Ex. `https://civitai.com/api/download/models/90854`
- `HuggingFace`. Private models are supported if you provide an access token in `config.json` (`"hf_token": "TOKEN"`).
	- Ex. `https://huggingface.co/arenasys/demo/blob/main/AnythingV3.safetensors`
- `Google Drive`. They may block you, good luck.
	- Ex. `https://drive.google.com/file/d/1_sK-uEEZnS5mZThQbVg-2B-dV7qmAVyJ/view?usp=sharing`
- `Mega.nz`. URL must include the key.
	- Ex. `https://mega.nz/file/W1QxVZpL#E-B6XmqIWii3-mnzRtWlS2mQSrgm17sX20unA14fAu8`
- `Other`. All other URLs get downloaded with `curl -OJL URL`, so simple file hosts will work.

### Overview
- Stable diffusion 1.x and 2.x (including v-prediction)
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
- ~~Merging~~ (working on it!)