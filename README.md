## Qt GUI for Stable diffusion
--------
Built from the ground up alongside [sd-inference-server](https://github.com/arenasys/sd-inference-server), the backend for this GUI.
![example](https://github.com/arenasys/qDiffusion/raw/master/source/screenshot.png)
## Getting started
### Install
1. [Download](https://github.com/arenasys/qDiffusion/archive/refs/heads/master.zip) this repo as a zip and extract it.
2. Run `qDiffusion.exe` (or `bash ./source/start.sh` on Linux).
	- First time users will need to wait for Python and PyQt5 to be downloaded.
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

### Remote
Notebooks for running a remote instance are available: [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb), [Kaggle](https://www.kaggle.com/code/arenasys/qdiffusion)

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
	- If issues persist after a remake it could be the cloudflare tunnel is down, check [Here](https://www.cloudflarestatus.com/).
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