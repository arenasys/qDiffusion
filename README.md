## Qt GUI for Stable diffusion
--------
Built from the ground up alongside [sd-inference-server](https://github.com/arenasys/sd-inference-server), the backend for this GUI.
![example](https://github.com/arenasys/qDiffusion/raw/master/screenshot.png)

### Install
Clone the repo via `git clone https://github.com/arenasys/qDiffusion`. Then run `qDiffusion`. Three modes are available: `Nvidia, AMD, and Remote`. Remote will only install whats needed to connect to a remote instance (much lighter). The `start_win.bat` and `start_linux.sh` launchers are equivalent to the exe (but less cool).

### Remote
Notebooks for running a remote instances are available: [Colab](https://colab.research.google.com/github/arenasys/qDiffusion/blob/master/remote_colab.ipynb).

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
- ~~ControlNet~~ (working on it!)
- ~~Merging~~ (working on it!)