import os
import re
import random
import copy
import json

import PIL.Image
import PIL.PngImagePlugin

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QVariant, QSize
from PyQt5.QtQml import qmlRegisterUncreatableType, qmlRegisterType

IDX = -1

LABELS = [
    ("prompt", "Prompt"),
    ("negative_prompt", "Negative prompt"),
    ("steps", "Steps"),
    ("sampler", "Sampler"),
    ("eta", "Eta"),
    ("scale", "CFG scale"),
    ("seed", "Seed"),
    ("size", "Size"),
    ("model", "Model"),
    ("UNET", "UNET"),
    ("VAE", "VAE"),
    ("CLIP", "CLIP"),
    ("mode", "Mode"),
    ("inputs", "Inputs"),
    ("subseed", "Variation seed"),
    ("subseed_strength", "Variation seed strength"),
    ("strength", "Denoising strength"),
    ("clip_skip", "Clip skip"),
    ("hr_resize", "Hires resize"),
    ("hr_factor", "Hires factor"),
    ("hr_strength", "Hires strength"),
    ("hr_upscaler", "Hires upscaler"),
    ("hr_sampler", "Hires sampler"),
    ("hr_steps", "Hires steps"),
    ("hr_scale", "Hires CFG scale"),
    ("hr_model", "Hires Model"),
    ("hr_cfg_rescale", "Hires CFG rescale"),
    ("hr_prediction_type", "Hires Prediction type"),
    ("img2img_upscaler", "Upscaler"),
    ("cfg_rescale", "CFG rescale"),
    ("prediction_type", "Prediction type")
]

SETTABLE = [
    "size", "prompt", "negative_prompt", "steps", "sampler", "schedule", "scale", "seed", "width", "height",
    "model", "UNET", "VAE", "CLIP", "model", "subseed", "subseed_strength", "strength", "eta", "clip_skip", "img2img_upscaler",
    "hr_factor", "hr_strength", "hr_upscaler", "hr_sampler", "hr_steps", "hr_scale", "hr_model",
    "cfg_rescale", "prediction_type"
]

def formatParameters(json):
    json = copy.deepcopy(json)

    formatted = ""
    if "prompt" in json:
        formatted = json["prompt"] + "\n"
        formatted += "Negative prompt: " + json["negative_prompt"] + "\n"

    if "mode" in json:
        json["mode"] = json["mode"].capitalize().replace("Txt2img", "Txt2Img").replace("Img2img", "Img2Img")

    if "inputs" in json:
        json["inputs"] = " + ".join([i.capitalize().replace("Controlnet", "ControlNet") for i in json["inputs"]])

    json["size"] = f"{json['width']}x{json['height']}"

    params = []
    for k, label in LABELS:
        if k == "prompt" or k == "negative_prompt":
            continue
        if k in json:
            v = json[k]
            if type(v) == list:
                v = ", ".join([str(i) for i in v])

            params += [f"{label}: {v}"]
    formatted += ', '.join(params)
    return formatted

def parseParameters(formatted):
    params, positive, negative = "", "", ""

    blocks = re.split(r"^(?=[\w\s]+:)", "Prompt: "+formatted, flags=re.MULTILINE)
    for b in blocks:
        if not b:
            continue
        d = b.split(":",1)[-1].strip()
        if b.startswith("Prompt:"):
            positive = d
        if b.startswith("Negative prompt:"):
            negative = d
        if b.startswith("Steps:"):
            params = b
    
    json = {}
    json["prompt"] = positive
    json["negative_prompt"] = negative

    p = params.split(":")
    for i in range(1, len(p)):
        label = p[i-1].rsplit(",", 1)[-1].strip()
        value = p[i].rsplit(",", 1)[0].strip()
        name = None
        for n, l in LABELS:
            if l == label:
                name = n
        if name:
            json[name] = value
    
    return json

def getParameters(img):
    params = img.text("parameters")
    if not params and img.text("Description"):
        desc = img.text("Description").replace("(","\\(").replace(")","\\)").replace("{","(").replace("}",")")
        data = json.loads(img.text("Comment"))
        uc = data['uc'].replace("(","\\(").replace(")","\\)").replace("{","(").replace("}",")")
        params = f"{desc}\nNegative prompt: {uc}\nSteps: {data['steps']}, Sampler: {data['sampler']}, CFG scale: {data['scale']}, Seed: {data['seed']}"
        if "strength" in data:
            params += f", Denoising strength: {data['strength']}"
    return params

def formatRecipe(metadata):
    checkpoint_recipe = metadata.get("merge_checkpoint_recipe","")
    lora_recipe = metadata.get("merge_lora_recipe","")
    lora_strength = metadata.get("merge_lora_strength","")
    if lora_recipe and lora_strength:
        recipe = {
            "type": "LoRA",
            "operations": lora_recipe,
            "strength": lora_strength
        }
    elif checkpoint_recipe:
        recipe = {
            "type": "Checkpoint",
            "operations": checkpoint_recipe
        }
    else:
        return ""
    
    return json.dumps(recipe)

def getIndex(folder):
    def get_idx(filename):
        try:
            return int(filename.split(".")[0].split("-")[0])
        except Exception:
            return 0

    idx = max([get_idx(f) for f in os.listdir(folder)] + [0]) + 1
    return idx

def getExtent(bound, padding, src, wrk):
    if padding == None or padding < 0:
        padding = 10240

    wrk_w, wrk_h = wrk
    src_w, src_h = src

    x1, y1, x2, y2 = bound

    ar = wrk_w/wrk_h
    cx,cy = x1 + (x2-x1)//2, y1 + (y2-y1)//2
    rw,rh = min(src_w, (x2-x1)+padding), min(src_h, (y2-y1)+padding)

    if wrk_w/rw < wrk_h/rh:
        w = rw
        h = int(w/ar)
        if h > src_h:
            h = src_h
            w = int(h*ar)
    else:
        h = rh
        w = int(h*ar)
        if w > src_w:
            w = src_w
            h = int(w/ar)

    x1 = cx - w//2
    x2 = cx + w - (w//2)

    if x1 < 0:
        x2 += -x1
        x1 = 0
    if x2 > src_w:
        x1 -= x2-src_w
        x2 = src_w

    y1 = cy - h//2
    y2 = cy + h - (h//2)

    if y1 < 0:
        y2 += -y1
        y1 = 0
    if y2 > src_h:
        y1 -= y2-src_h
        y2 = src_h

    return int(x1), int(y1), int(x2), int(y2)

class VariantMap(QObject):
    updating = pyqtSignal(str, 'QVariant', 'QVariant')
    updated = pyqtSignal(str)
    def __init__(self, parent=None, map = {}, strict=False):
        super().__init__(parent)
        self._map = map
        self._strict = strict

    @pyqtSlot(str, result='QVariant')
    def get(self, key, default=QVariant()):
        if key in self._map:
            return self._map[key]
        return default
    
    @pyqtSlot(str, 'QVariant')
    def set(self, key, value):
        if key in self._map and self._map[key] == value:
            return

        if key in self._map:
            if self._strict:
                try:
                    value = type(self._map[key])(value)
                except Exception:
                    pass
            self.updating.emit(key, self._map[key], value)
        else:
            self.updating.emit(key, QVariant(), value)

        self._map[key] = value
        self.updated.emit(key)

class ParametersItem(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, name="", label="", value=""):
        super().__init__(parent)
        self._name = name
        self._label = label
        self._value = value
        self._checked = True

    @pyqtProperty(str, notify=updated)
    def name(self):
        return self._name

    @pyqtProperty(str, notify=updated)
    def label(self):
        return self._label
            
    @pyqtProperty(str, notify=updated)
    def value(self):
        return self._value

    @pyqtProperty(bool, notify=updated)
    def checked(self):
        return self._checked
    
    @checked.setter
    def checked(self, checked):
        self._checked = checked
        self.updated.emit()

class ParametersParser(QObject):
    updated = pyqtSignal()
    success = pyqtSignal()
    def __init__(self, parent=None, formatted=None, json=None):
        super().__init__(parent)
        self._parameters = []

        if formatted:
            self._formatted = formatted
            self.parseFormatted()
        else:
            self._formatted = ""

        if json:
            self._json = json
            self.parseJson()
        else:
            self._json = {}

    @pyqtProperty(str, notify=updated)
    def formatted(self):
        return self._formatted

    @formatted.setter
    def formatted(self, formatted):
        if formatted != self._formatted:
            self._formatted = formatted
            self.parseFormatted()
            
    @pyqtProperty(object, notify=updated)
    def json(self):
        return self._json

    @json.setter
    def json(self, json):
        if json != self._json:
            self._json = json
            self._parseJson()
    
    @pyqtProperty(list, notify=updated)
    def parameters(self):
        return self._parameters
    
    def parseFormatted(self):
        self._json = parseParameters(self._formatted)
        if len(self._json) == 2:
            return False

        self._parameters = []

        for n, v in self._json.items():
            l = None
            for name, label in LABELS:
                if name == n and name in SETTABLE:
                    l = label
                    break
            else:
                continue
            self._parameters += [ParametersItem(self, n, l, v)]

        reset = ParametersItem(self, "reset", "Reset others?", "")
        reset._checked = False

        self._parameters += [reset]

        self.updated.emit()

        if self._parameters != []:
            self.success.emit()
            return True
        else:
            return False
    
class Parameters(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, source=None):
        super().__init__(parent)
        
        self.gui = parent
        if self.gui:
            self.gui.optionsUpdated.connect(self.optionsUpdated)

        self._client_only = [
            "models", "samplers", "UNETs", "CLIPs", "VAEs", "SRs", "SR", "LoRAs", "LoRA", "TIs", "TI", "CN", "CNs", "hr_upscalers", "img2img_upscalers", 
            "attentions", "device", "devices", "batch_count", "prompt", "negative_prompt", "vram_usages", "artifact_modes", "preview_modes", "schedules",
            "CN_modes", "CN_preprocessors", "vram_modes", "true_samplers", "schedule", "network_modes", "model", "output_folder", "mask_fill_modes", "autocast_modes",
            "prediction_types", "tiling_modes", "precisions", "fetching_modes", "model_modes", "Refiners", "model_types", "Detailers", "Detailer"
        ]

        self._adv_only = [
            "tome_ratio", "tiling_mode", "vae_precision", "precision", "subseed_strength", "subseed", 
            "hr_sampler", "hr_scale"
        ]
        self._default_values = {
            "prompt":"", "negative_prompt":"", "width": 512, "height": 512, "steps": 25, "scale": 7.0, "strength": 0.5, "seed": -1, "eta": 1.0,
            "hr_factor": 1.0, "hr_strength":  0.7, "hr_sampler": "Euler a", "hr_steps": 25, "hr_scale": 7.0, "clip_skip": 1, "batch_size": 1, "padding": -1, "mask_blur": 4, "mask_expand": 0, "subseed":-1, "subseed_strength": 0.0,
            "sampler": "Euler a", "samplers":[], "hr_upscaler":"Lanczos", "hr_upscalers":[], "img2img_upscaler":"Lanczos", "img2img_upscalers":[],
            "model":"", "models":[], "UNET":"", "UNETs":[], "CLIP":"", "CLIPs":[], "VAE":"", "VAEs":[], "LoRA":[], "LoRAs":[], "SR":[], "SRs":[], "TI":"", "TIs":[],
            "attention":"", "attentions":[], "device":"", "devices":[], "batch_count": 1, "schedule": "Linear", "schedules": ["Linear", "Karras", "Exponential"],
            "vram_mode": "Default", "vram_modes": ["Default", "Minimal"], "artifact_mode": "Disabled", "artifact_modes": ["Disabled", "Enabled"], "preview_mode": "Light",
            "preview_modes": ["Disabled", "Light", "Medium", "Full"], "preview_interval":1, "true_samplers": [], "true_sampler": "Euler a",
            "network_mode": "Static", "network_modes": ["Dynamic", "Static"], "mask_fill": "Original", "mask_fill_modes": ["Original", "Noise"],
            "tome_ratio": 0.0, "hr_model": "", "cfg_rescale": 0.0, "output_folder": "", "autocast": "Disabled", "autocast_modes": ["Disabled", "Enabled"],
            "CN_modes": ["Canny", "Depth", "Pose", "Lineart", "Softedge", "Anime", "M-LSD", "Instruct", "Shuffle", "Inpaint", "Scribble", "Normal", "Tile", "QR"],#, "Segmentation"]
            "CN_preprocessors": ["None", "Invert", "Canny", "Depth", "Pose", "Lineart", "Softedge", "Anime", "M-LSD", "Shuffle", "Scribble", "Normal"],
            "prediction_type": "Default", "prediction_types": ["Default", "Epsilon", "V"], "tiling_mode": "Disabled", "tiling_modes": ["Disabled", "Enabled"],
            "precisions": ["FP16", "FP32"], "vae_precision": "FP16", "precision": "FP16", "fetching_mode": "Dont Wait", "fetching_modes": ["Wait", "Dont Wait"],
            "model_mode": "Standard", "model_modes": ["Standard", "Refiner"], "Refiner": "", "Refiners": [], "model_types": {}, "Detailers": [], "Detailer": ""
        }

        if source:
            self._default_values = source._values._map.copy()

        self._values = VariantMap(self, self._default_values.copy(), strict=True)
        self._values.updating.connect(self.mapsUpdating)
        self._values.updated.connect(self.onUpdated)
        self._availableNetworks = []
        self._activeNetworks = []
        self._activeDetailers = []
        self._active = []

    def resolution(self):
        w, h = self.values.get("width"), self.values.get("height")
        if self.gui.config.get("always_hr_resolution", True):
            factor = self.values.get("hr_factor")
            w = int(w * factor)
            h = int(h * factor)
        return QSize(w,h)

    @pyqtSlot()
    def promptsChanged(self):
        positive = self._values.get("prompt")
        negative = self._values.get("negative_prompt")

        netre = r"<@?(lora):([^:>]+)(?::([-\d.]+))?(?::([-\d.]+))?>"

        nets = re.findall(netre, positive) + re.findall(netre, negative)
        self._activeNetworks = []
        for net in nets:
            for a in self._availableNetworks:
                if net[1] + "." in a:
                    self._activeNetworks += [a]
                    break
        self.updated.emit()

    @pyqtProperty(list, notify=updated)
    def availableNetworks(self):
        return self._availableNetworks

    @pyqtProperty(list, notify=updated)
    def activeNetworks(self):
        return self._activeNetworks
    
    @pyqtProperty(list, notify=updated)
    def activeDetailers(self):
        return self._activeDetailers
    
    @pyqtProperty(list, notify=updated)
    def active(self):
        return self._active
    
    @pyqtSlot(str)
    def addNetwork(self, net):
        if not net in self._availableNetworks:
            return
        if net in self._activeNetworks:
            return
        
        name = self.gui.modelName(net)        
        self._values.set("prompt", self._values.get("prompt") + f"<lora:{name}:1.0>")   

    @pyqtSlot(int)
    def deleteNetwork(self, index):
        net = self._activeNetworks[index]
        name = self.gui.modelName(net)

        netre = fr"(?:\s)?<@?(lora):({name})(?::([-\d.]+))?(?::([-\d.]+))?>"
        positive = re.sub(netre,'',self._values.get("prompt"))
        negative = re.sub(netre,'',self._values.get("negative_prompt"))

        self._values.set("prompt", positive)
        self._values.set("negative_prompt", negative)

    @pyqtSlot(str)
    def addDetailer(self, detailer):
        self.doActivate(detailer)
        self.getActive()

    @pyqtSlot(int)
    def deleteDetailer(self, index):
        self.doDeactivate(self._activeDetailers[index])
        self.getActive()
    
    @pyqtProperty(VariantMap, notify=updated)
    def values(self):
        return self._values

    @pyqtSlot(str, 'QVariant', 'QVariant')
    def mapsUpdating(self, key, prev, curr):
        changed = False
        pairs = [("true_sampler", "hr_sampler"), ("steps", "hr_steps"), ("scale", "hr_scale"), ("UNET", "hr_model")]
        for src, dst in pairs:
            if key == src:
                val = self._values.get(dst)
                if val == prev or (type(val) == float and abs(val - prev) < 0.001):
                    changed = True
                    self._values.set(dst, curr)

        if changed:
            self.updated.emit()

    @pyqtSlot(str)
    def onUpdated(self, key):
        self.getActive()

        if key != "sampler" and key != "schedule":
            return

        if key == "sampler":
            sampler = self._values.get("sampler")
            schedules = ["Linear", "Karras", "Exponential"]
            default_scheduler = "Linear"

            if sampler in {"DDIM", "PLMS"}:
                schedules = ["Linear"]
            elif "DPM" in sampler:
                default_scheduler = "Karras"
            
            self._values.set("schedules", schedules)
            self._values.set("schedule", default_scheduler)

        true_sampler = self._values.get("sampler")
        schedule = self._values.get("schedule")
        if schedule and schedule != "Linear":
            true_sampler += " " + schedule
        self._values.set("true_sampler", true_sampler)
        

    @pyqtSlot()
    def optionsUpdated(self):
        if not self.gui._options:
            return

        for k in self.gui._options:
            kk = k + "s"
            if kk in self._values._map:
                opts = self.gui._options[k]
                if k in {"UNET", "CLIP", "VAE", "SR", "LoRA", "TI"}:
                    opts = sorted(opts, key=lambda m: self.gui.modelName(m.lower()))
                self._values.set(kk, opts)
                if (not self._values.get(k) or not self._values.get(k) in self.gui._options[k]) and self.gui._options[k]:                   
                    if k in {"UNET", "CLIP", "VAE"} and self._values.get("model"):
                        self._values.set("model", "")
                    if k in self._default_values and self._default_values[k] in self.gui._options[k]:
                        self._values.set(k, self._default_values[k])
                    else:
                        self._values.set(k, self.gui._options[k][0])
        models = []
        for k in self.gui._options["UNET"]:
            if k in self.gui._options["CLIP"] and k in self.gui._options["VAE"]:
                models += [k]
        self._values.set("models", models)

        self._values.set("model_types", self.gui._options.get("model_types", {}))

        unets = self._values.get("UNETs")
        unets = [u for u in unets if not u in models] + [u for u in unets if u in models]
        self._values.set("UNETs", unets)

        vaes = self._values.get("VAEs")
        vaes = [v for v in vaes if not v in models] + [v for v in vaes if v in models]
        self._values.set("VAEs", vaes)

        clips = self._values.get("CLIPs")
        clips = [c for c in clips if not c in models] + [c for c in clips if c in models]
        self._values.set("CLIPs", clips)

        refiners = [c for c in unets if "refiner" in c.lower()]
        refiner = self._values.get("Refiner")
        self._values.set("Refiners", refiners)
        if not refiners:
            refiner = None
        elif not refiner in refiners:
            refiner = refiners[0]
        self._values.set("Refiner", refiner)

        if models and (not self._values.get("model") or not self._values.get("model") in models):
            model = self.gui.filterFavourites(models)[0]
            self._values.set("model", model)
            self._values.set("UNET", model)
            self._values.set("VAE", model)
            self._values.set("CLIP", model)

        self._availableNetworks = self._values.get("LoRAs")
        self._activeNetworks = [n for n in self._activeNetworks if n in self._availableNetworks]

        if self._values.get("img2img_upscaler") not in self._values.get("img2img_upscalers"):
            self._values.set("img2img_upscaler", "Lanczos")

        if self._values.get("hr_upscaler") not in self._values.get("hr_upscalers"):
            self._values.set("hr_upscaler", "Latent (nearest)")

        config = [
            ("device", "device", "devices"),
            ("artifacts", "artifact_mode", "artifact_modes"),
            ("previews", "preview_mode", "preview_modes"),
            ("preview_interval", "preview_interval", None),
            ("vram", "vram_mode", "vram_modes"),
            ("attention", "attention", "attentions"),
            ("precision", "precision", "precisions"),
            ("vae_precision", "vae_precision", "precisions"),
            ("vae_tiling", "tiling_mode", "tiling_modes"),
            ("fetching", "fetching_mode", "fetching_modes"),
            ("output_folder", "output_folder", None)
        ]

        remote = self.gui.config.get("mode", "").lower() == "remote"
        for cfg, key, opts in config:
            val = self.gui.config.get(cfg, None)
            if val and (not opts or val in self._values.get(opts)):
                self._values.set(key, val)
            elif cfg == "preview_interval" and remote:
                self._values.set(key, 5)

        self._values.set("true_samplers", self._values.get("samplers"))
        self._values.set("samplers", [s for s in self._values.get("samplers") if not "Karras" in s and not "Exponential" in s])

        self.updated.emit()

    def buildPrompts(self, batch_size=1, seed=-1):
        pos = self.parsePrompt(self._values._map['prompt'], batch_size, seed)
        neg = self.parsePrompt(self._values._map['negative_prompt'], batch_size, seed)
        return list(zip(pos, neg))

    def buildRequest(self, batch_size, seed, images=[], masks=[], areas=[], control=[]):
        request = {}
        data = {}

        for k, v in self._values._map.items():
            if not k in self._client_only:
                data[k] = v

        data['batch_size'] = int(batch_size)
        data['seed'] = seed

        data['prompt'] = self.buildPrompts(batch_size, seed)

        data["sampler"] = data["true_sampler"]
        del data["true_sampler"]

        if (data["steps"] == 0 or data["strength"] == 0.0) and images:
            request["type"] = "upscale"
            data["image"] = images
            if any(masks):
                data["mask"] = masks
        elif images:
            request["type"] = "img2img"
            data["image"] = images
            if any(masks):
                data["mask"] = masks
        else:
            request["type"] = "txt2img"
        
        if request["type"] == "txt2img" and self._activeDetailers:
            data["detailers"] = self._activeDetailers
            basic = [t for t in self.gui.tabs if t.name == "Generate"][0]
            data["detailer_parameters"] = [
                basic.detailers.getSettings(d) for d in self._activeDetailers
            ]

        if request["type"] != "txt2img" and self.gui.config.get("always_hr_resolution", True):
            factor = data['hr_factor']
            data['width'] = int(data['width'] * factor)
            data['height'] = int(data['height'] * factor)

        if any(areas):
            s = len(self.subprompts)
            for a in range(len(areas)):
                if areas[a] and len(areas[a]) > s:
                    areas[a] = areas[a][:s]
            data["area"] = areas

        if not request["type"] == "img2img" and not "area" in data:
            del data["mask_blur"]
            del data["mask_expand"]
        if not "mask" in data:
            del data["mask_fill"]

        if data["hr_factor"] == 1.0:
            for k in list(data.keys()):
                if k.startswith("hr_"):
                    del data[k]
        else:
            if data["hr_steps"] == data["steps"]:
                del data["hr_steps"]
            if data["hr_sampler"] == data["sampler"]:
                del data["hr_sampler"]
            if data["hr_scale"] == data["scale"]:
                del data["hr_scale"]
            if data["hr_model"] == data["UNET"]:
                del data["hr_model"]
            else:
                hr_model_name = self.gui.modelName(data["hr_model"])
                defaults = self.gui.getDefaults(hr_model_name)
                for k,v in defaults.items():
                    kk = "hr_" + k
                    data[kk] = v
        
        if not request["type"] in {"img2img", "upscale"}:
            del data["img2img_upscaler"]
        
        if data["eta"] == 1.0:
            del data["eta"]

        if data["padding"] == -1:
            if "detailers" in data:
                data["padding"] = 32
            else:
                del data["padding"]
        
        if data["subseed_strength"] == 0.0:
            del data["subseed"]
            del data["subseed_strength"]

        data["device_name"] = self._values.get("device")

        if control:
            images = []
            opts = []
            models = []

            for m,o,i in control:
                models += [m]
                opts += [o]
                images += [i]

            if "Tile" in models:
                opts = opts[models.index("Tile")]
                data["tile_strength"] = opts["scale"]
                data["tile_size"] = opts["args"][0]
                data["tile_upscale"] = opts["args"][1]
                data["tile_guess"] = opts["guess"]
            else:
                data["cn_image"] = images
                data["cn"] = models
                data["cn_opts"] = opts

        if request["type"] != "img2img" and "strength" in data:
            del data["strength"]

        if data["artifact_mode"] == "Enabled":
            data["keep_artifacts"] = True
        del data["artifact_mode"]

        if request["type"] in {"txt2img", "img2img", "upscale"} and self.gui.isRemote:
            if data["fetching_mode"] == "Dont Wait":
                data["delay_fetch"] = True
        del data["fetching_mode"]

        if data["preview_mode"] != "Disabled":
            data["show_preview"] = data["preview_mode"]
        del data["preview_mode"]

        for k in self._adv_only:
            if k in data and not self.gui.config.get("advanced"):
                del data[k]

        if not self.gui.config.get("advanced") and data["prediction_type"] != "V":
            del data["cfg_rescale"]

        for k in ["tome_ratio", "cfg_rescale", "prediction_type", "tiling_mode", "vae_precision", "precision"]:
            if k in data and data[k] in {0.0, "Default"}:
                del data[k]

        data["autocast"] = data["autocast"] == "Enabled"

        if request["type"] == "upscale":
            for k in list(data.keys()):
                if not k in {"img2img_upscaler", "width", "height", "image", "mask", "mask_blur", "padding", "device_name"}:
                    del data[k]

        if "Refiner" in data and data["model_mode"] != "Refiner":
            del data["Refiner"]
        
        data = {k.lower():v for k,v in data.items()}

        request["data"] = data

        return request

    def buildAnnotateRequest(self, mode, args, image):
        data = {
            "cn_image": [image],
            "cn_annotator": [mode],
            "cn_args": [args],
            "device_name": self._values.get("device")
        }
        return {"type":"annotate", "data": data}

    @pyqtSlot()
    def reset(self):
        pass

    @pyqtSlot(list)
    def sync(self, params):
        processed = {}

        for p in params:
            entries = {p._name: (p._value, p._checked)}

            if p._name == "size":
                w,h = p._value.split("x")

                entries = {
                    "width": (int(w), p._checked),
                    "height": (int(h), p._checked),
                }
            
            if p._name == "hr_resize":
                hr_w, hr_h = p._value.split("x")
                hr_w, hr_h = int(hr_w), int(hr_h)

                if "width" in processed and processed["width"][1]:
                    w,h = self.processed["width"][0], self.processed["height"][0]
                else:
                    w,h = self.values.get("width"), self.values.get("height")

                f = (((hr_w/w) + (hr_h/h))/2)
                f = int(f / 0.005) * 0.005

                entries = {
                    "hr_factor": (f, p._checked)
                }
            
            if p._name == "sampler":
                if p._value.endswith(" Karras"):
                    sampler = p._value.rsplit(" ",1)[0]
                    schedule = "Karras"
                elif p._value.endswith(" Exponential"):
                    sampler = p._value.rsplit(" ",1)[0]
                    schedule = "Exponential"  
                else:
                    sampler = p._value
                    schedule = "Linear"
                
                entries = {
                    "sampler": (sampler, p._checked),
                    "schedule": (schedule, p._checked)
                }
            
            if p._name == "model":
                entries = {
                    "UNET": (p._value, p._checked),
                    "CLIP": (p._value, p._checked),
                    "VAE": (p._value, p._checked),
                }
            
            for n in entries:
                processed[n] = entries[n]
        
        reset = processed["reset"][1]
        del processed["reset"]
        
        for k in ["UNET", "CLIP", "VAE", "hr_model"]:
            if not k in processed:
                continue

            value, checked = processed[k]

            a = k + "s"
            if not a in self._values._map:
                a = "UNETs"

            available = self._values._map[a]
            closest_match = self.gui.closestModel(value, available)
            processed[k] = (closest_match, checked)

        if not "model" in processed and "UNET" in processed:
            value, checked = processed["UNET"]
            processed["model"] = (value, checked)

        for k in ["img2img_upscaler", "hr_upscaler"]:
            if not k in processed:
                continue

            value, checked = processed[k]
            available = self._values._map[k+"s"]
            if value in available:
                continue
            closest_match = self.gui.closestModel(value, available)
            if not closest_match and available:
                closest_match = available[0]
            processed[k] = (closest_match, checked)
        
        for name in SETTABLE:
            value = None

            if name in processed and processed[name][1]:
                value = processed[name][0]
            
            if value == None and reset:
                if name == "hr_steps":
                    value = self.values.get("steps")
                elif name == "hr_sampler":
                    value = self.values.get("sampler")
                elif name == "hr_scale":
                    value = self.values.get("scale")
                elif name in self._default_values:
                    value = self._default_values.get(name)

            if value == None:
                continue

            try:
                value = type(self.values.get(name))(value)
                self.values.set(name, value)
            except Exception as e:
                pass

        self.updated.emit()

    def parsePrompt(self, prompt, batch_size, seed):
        wildcards = self.gui.wildcards._wildcards
        counter = self.gui.wildcards._counter
        prompts = []
        file_pattern = re.compile(r"@?__([^\s]+?)__(?!___)")
        inline_pattern = re.compile(r"{([^{}|]+(?:\|[^{}|]+)*)}")
        seed = random.randrange(2147483646) if seed == -1 else seed
        
        for i in range(batch_size):
            roll = random.Random(seed+i)

            sp = self.parseSubprompts(str(prompt))
            for j in range(len(sp)):
                p = sp[j]

                while m := inline_pattern.search(p):
                    p = list(p)
                    s,e = m.span(0)
                    options = m.group(1).split("|")
                    p[s:e] = roll.choice(options)
                    p = ''.join(p)

                while m := file_pattern.search(p):
                    s,e = m.span(0)
                    name = m.group(1)
                    p = list(p)
                    c = []
                    if name in wildcards:
                        if p[s] == "@":
                            if not name in counter:
                                counter[name] = 0
                            c = wildcards[name][counter[name]%len(wildcards[name])]
                            counter[name] += 1
                        else:
                            c = roll.choice(wildcards[name])
                    p[s:e] = c
                    p = ''.join(p)
                sp[j] = p
            prompts += [sp]
        return prompts
    
    def parseSubprompts(self, p):
        return [s.replace('\n','').replace('\r', '').strip() for s in re.split("\sAND\s", p + " ")]
    
    @pyqtProperty(list, notify=updated)
    def subprompts(self):
        p = self._values.get("prompt")
        p = self.parseSubprompts(p)
        if len(p) <= 1:
            return []
        return p[1:]

    @pyqtSlot()
    def getActive(self):
        last = set(self._active)
        self._active = []

        prompt = self._values.get("prompt") + " " + self._values.get("negative_prompt")

        for lora_match in re.findall(r"<@?lora:([^:>]+)([^>]+)?>", prompt):
            for lora in self._values.get("LoRAs"):
                if lora_match[0] == lora.rsplit(os.path.sep,1)[-1].rsplit(".",1)[0]:
                    self._active += [lora]
        
        for w_match in re.findall(r"@?__([^\s]+?)__(?!___)", prompt):
            if w_match in self.gui.wildcards._wildcards:
                file = self.gui.wildcards._sources[w_match]
                self._active += [os.path.join("WILDCARD", file)]

        for emb in self._values.get("TIs"):
            if self.gui.modelName(emb) in prompt:
                self._active += [emb]

        for model in [self._values.get(m) for m in ["UNET", "VAE", "CLIP"]]:
            if model and not model in self._active:
                self._active += [model]
        
        hr = self._values.get("hr_upscaler")
        img = self._values.get("img2img_upscaler")
        sr = self._values.get("SRs")
        if hr in sr:
            self._active += [hr]
        if img in sr:
            self._active += [img]

        self._active += self._activeDetailers

        if set(self._active) != last:
            self.updated.emit()

    @pyqtSlot(str)
    def doActivate(self, file):
        def append(s, key="prompt"):
            prompt = self._values.get(key)
            if prompt:
                s = ", " + s
            self._values.set(key, prompt + s)
        
        name = self.gui.modelName(file)

        for m in ["UNET", "VAE", "CLIP"]:
            if file in self._values.get(m + "s"):
                self._values.set(m, file)
        self._values.set("model", self._values.get("UNET"))

        if file in self._values.get("LoRAs"):
            append(f"<lora:{name}>")

        if file in self._values.get("TIs"):
            if "neg" in file.rsplit(os.path.sep, 1)[0].lower():
                append(name, "negative_prompt")
            else:
                append(name)

        if file in self._values.get("SRs"):
            self._values.set("hr_upscaler", file)
            self._values.set("img2img_upscaler", file)

        name = file.split(os.path.sep,1)[-1].rsplit('.',1)[0].replace(os.path.sep, "/")
        if file.startswith("WILDCARD") and name in self.gui.wildcards._wildcards:
            append(f"__{name}__")
        
        if file in self._values.get("Detailers") and not file in self._activeDetailers:
            self._activeDetailers += [file]
        
    @pyqtSlot(str)
    def doDeactivate(self, file):
        def remove(m):
            m = fr"(,*\s*{m})"
            c = r"(^,*\s*)|(,*\s*$)"
            pos = re.sub(c,'',re.sub(m,'',self._values.get("prompt")))
            neg = re.sub(c,'',re.sub(m,'',self._values.get("negative_prompt")))
            self._values.set("prompt", pos)
            self._values.set("negative_prompt", neg)
        
        name = self.gui.modelName(file)

        if file in self._values.get("VAEs"):
            self._values.set("VAE", self._values.get("UNET"))

        if file in self._values.get("LoRAs"):
            remove(fr"<@?lora:({re.escape(name)})(?::([-\d.]+))?(?::([-\d.]+))?>")

        if file in self._values.get("TIs"):
            remove(fr"{re.escape(name)}")

        if file in self._values.get("SRs"):
            self._values.set("hr_upscaler", "Latent (nearest)")
            self._values.set("img2img_upscaler", "Lanczos")

        name = file.split(os.path.sep,1)[-1].rsplit('.',1)[0].replace(os.path.sep, "/")
        if file.startswith("WILDCARD") and name in self.gui.wildcards._wildcards:
            remove(fr"__{re.escape(name)}__")

        if file in self._activeDetailers:
            self._activeDetailers.remove(file)

    @pyqtSlot(str)
    def doToggle(self, file):
        if file in self._active:
            self.doDeactivate(file)
        else:
            self.doActivate(file)
        
        self.getActive()

    def copy(self):
        out = Parameters(None, self)
        out.gui = self.gui
        return out
        
def registerTypes():
    qmlRegisterUncreatableType(Parameters, "gui", 1, 0, "ParametersMap", "Not a QML type")
    qmlRegisterUncreatableType(VariantMap, "gui", 1, 0, "VariantMap", "Not a QML type")
    qmlRegisterUncreatableType(ParametersItem, "gui", 1, 0, "ParametersItem", "Not a QML type")
    qmlRegisterType(ParametersParser, "gui", 1, 0, "ParametersParser")