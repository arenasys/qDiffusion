## Qt GUI for Stable diffusion
--------
Built from the ground up alongside [sd-inference-server](https://github.com/arenasys/sd-inference-server), the backend for this GUI.
![example](https://github.com/arenasys/qDiffusion/raw/master/screenshot.png)

### Install
Clone or [Download](https://github.com/arenasys/qDiffusion/archive/refs/heads/master.zip) this repo. Then run `qDiffusion`. Three modes are available: `Nvidia, AMD, and Remote`. Remote will only install whats needed to connect to a remote instance (much lighter). The `start_win.bat` and `start_linux.sh` launchers are mostly equivalent to the exe (but less cool).

### Remote
Notebooks for running a remote instances are available: [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb), [Kaggle](https://www.kaggle.com/code/arenasys/qdiffusion)

### Details
**Startup**. qDiffusion is capable of installing from scratch, even without python installed. This is an automatic process:
1. `qDiffusion.exe`. Ensures python is available, downloading if needed. Then runs `launch.py`
2. `launch.py`. Ensures a venv is active and PyQT5 is installed. Then imports `main.py`
	- Qt cannot be loaded from paths containing unicode characters (`ユニコード`, etc)
	- The venv is installed at the base of the drive if this is detected (`C:\qDiffusion`)
3. `main.py`. Bootstraps the GUI:
	1. Starts the GUI in a minimal state. The splash screen is shown while QML sources are compiled.
	2. Ensures the requirements are met for the chosen mode (`Nvidia, AMD, or Remote`).
		- Install screen prompts the user to install missing requirements (`requirements_*.txt`)
		- Skipped if no venv is active. Forced to show if `config.json` contains `'show': true`
		- Versions are not enforced, so different versions of torch/diffusers/xformers can be used.
	3. Starts the full GUI `Main.qml`, `gui.py`. Tabs are initialized, loaded and connected to the GUI.

These stages can be skipped if needed by directly launching the python files: `python source\main.py`, etc.

**Backend**. The backend is started once the GUI is ready, and can be reloaded via `File->Reload`.

In local inference mode (`Nvidia or AMD`) the inference repo is cloned into `source\sd-inference-server`, then a child process called `LocalInference` is created to run the server (`local.py`). Communication happens directly between the GUI and inference processes, so the server is not exposed on any network interface. A separate process is required since python will freeze for multiple seconds when importing large libraries (`torch`, `diffusers`, etc).

In remote mode (`remote.py`) the inference repo is not cloned and there is no child process, instead a thread will run a websocket client and relay requests/responses to the remote websocket server (`server.py`), all messages are BSON encoded and encrypted for authentication (before TLS). Any websocket aware HTTP proxy can route these connections. The server is mostly stateless, each request is fully independent, and all responses are relayed back to the client without writing to the disk (except for some error logging). The exception is the models, which are managed between requests to reduce overhead and VRAM usage.

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