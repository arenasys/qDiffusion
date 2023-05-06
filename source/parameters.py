import io
import os
import re
import random
import datetime

import PIL.Image
import PIL.PngImagePlugin

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QVariant, QSize
from PyQt5.QtQml import qmlRegisterUncreatableType, qmlRegisterType
from PyQt5.QtGui import QGuiApplication
IDX = -1

LABELS = [
    ("prompt", "Prompt"),
    ("negative_prompt", "Negative prompt"),
    ("steps", "Steps"),
    ("sampler", "Sampler"),
    ("scale", "CFG scale"),
    ("seed", "Seed"),
    ("size", "Size"),
    ("model", "Model"),
    ("UNET", "UNET"),
    ("VAE", "VAE"),
    ("CLIP", "CLIP"),
    ("subseed", "Variation seed"),
    ("subseed_strength", "Variation seed strength"),
    ("strength", "Denoising strength"),
    ("clip_skip", "Clip skip"),
    ("lora", "LoRA"),
    ("lora_strength", "LoRA strength"),
    ("hn", "HN"),
    ("hn_strength", "HN strength"),
    ("hr_resize", "Hires resize"),
    ("hr_factor", "Hires factor"),
    ("hr_upscaler", "Hires upscaler"),
    ("hr_sampler", "Hires sampler"),
    ("hr_steps", "Hires steps"),
    ("hr_eta", "Hires sampler eta"),
    ("img2img_upscaler", "Upscaler"),
]
NETWORKS = {"LoRA":"lora","HN":"hypernet"}
NETWORKS_INV = {"lora":"LoRA","hypernet":"HN"}

def format_parameters(json):
    formatted = ""
    if "prompt" in json:
        formatted = json["prompt"] + "\n"
        formatted += "Negative prompt: " + json["negative_prompt"] + "\n"

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

def parse_parameters(formatted):
    lines = formatted.strip().split("\n")

    params = lines[-1]
    positive = []
    negative = []
    for line in lines[:-1]:
        if negative:
            negative += [line.strip()]
        elif line[0:17] == "Negative prompt: ":
            negative += [line[17:].strip()]
        else:
            positive += [line.strip()]
    
    json = {}
    json["prompt"] = "\n".join(positive)
    json["negative_prompt"] = "\n".join(negative)

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


def get_index(folder):
    def get_idx(filename):
        try:
            return int(filename.split(".")[0].split("-")[0])
        except Exception:
            return 0

    idx = max([get_idx(f) for f in os.listdir(folder)] + [0]) + 1
    return idx

def save_image(img, metadata, outputs):
    if type(img) == bytes:
        img = PIL.Image.open(io.BytesIO(img))
    m = PIL.PngImagePlugin.PngInfo()
    m.add_text("parameters", format_parameters(metadata))

    folder = os.path.join(outputs, metadata["mode"])
    os.makedirs(folder, exist_ok=True)

    idx = get_index(folder)
    name = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")

    tmp = os.path.join(folder, f"{name}.tmp")
    real = os.path.join(folder, f"{name}.png")

    img.save(tmp, format="PNG", pnginfo=m)
    os.replace(tmp, real)
    
    metadata["file"] = real

def get_extent(bound, padding, src, wrk):
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
    def __init__(self, parent=None, map = {}):
        super().__init__(parent)
        self._map = map

    @pyqtSlot(str, result='QVariant')
    def get(self, key):
        if key in self._map:
            return self._map[key]
        return QVariant()
    
    @pyqtSlot(str, 'QVariant')
    def set(self, key, value):
        if key in self._map and self._map[key] == value:
            return

        if key in self._map:
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
        self._json = parse_parameters(self._formatted)
        if len(self._json) == 2:
            return False

        self._parameters = []

        for n, v in self._json.items():
            l = None
            for name, label in LABELS:
                if name == n:
                    l = label
                    break
            else:
                continue
            self._parameters += [ParametersItem(self, n, l, v)]

        self.updated.emit()

        if self._parameters != []:
            self.success.emit()
            return True
        else:
            return False
    
class Parameters(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent

        self.gui.optionsUpdated.connect(self.optionsUpdated)

        self._client_only = [
            "models", "samplers", "UNETs", "CLIPs", "VAEs", "SRs", "SR", "LoRAs", "HNs", "LoRA", "HN", "TIs", "TI", "CN", "CNs", "hr_upscalers", "img2img_upscalers", 
            "attentions", "device", "devices", "batch_count", "prompt", "negative_prompt", "vram_usages", "artifact_modes", "preview_modes", "schedules",
            "CN_modes", "vram_modes", "true_samplers", "schedule"
        ]
        self._values = VariantMap(self, {
            "prompt":"", "negative_prompt":"", "width": 512, "height": 512, "steps": 25, "scale": 7, "strength": 0.75, "seed": -1, "eta": 1.0,
            "hr_factor": 1.0, "hr_strength":  0.7, "hr_sampler": "Euler a", "hr_steps": 25, "hr_eta": 1.0, "clip_skip": 1, "batch_size": 1, "padding": -1, "mask_blur": 4, "subseed":-1, "subseed_strength": 0.0,
            "model":"", "models":[], "sampler":"Euler a", "samplers":[], "hr_upscaler":"Latent (nearest)", "hr_upscalers":[], "img2img_upscaler":"Lanczos", "img2img_upscalers":[],
            "UNET":"", "UNETs":"", "CLIP":"", "CLIPs":[], "VAE":"", "VAEs":[], "LoRA":[], "LoRAs":[], "HN":[], "HNs":[], "SR":[], "SRs":[], "TI":"", "TIs":[], "CN":"", "CNs":[], "CN_modes": [],
            "attention":"", "attentions":[], "device":"", "devices":[], "batch_count": 1, "cn_strength":1.0, "schedule": "Default", "schedules": ["Default", "Karras"],
            "vram_mode": "Default", "vram_modes": ["Default", "Minimal"], "artifact_mode": "Disabled", "artifact_modes": ["Disabled", "Enabled"], "preview_mode": "Disabled",
            "preview_modes": ["Disabled", "Light", "Medium", "Full"], "preview_interval":1, "true_samplers": [], "true_sampler": "Euler a"
        })
        self._values.updating.connect(self.mapsUpdating)
        self._values.updated.connect(self.onUpdated)
        self._availableNetworks = []
        self._activeNetworks = []
        self._active = []

    @pyqtSlot()
    def promptsChanged(self):
        positive = self._values.get("prompt")
        negative = self._values.get("negative_prompt")

        netre = r"<@?(lora|hypernet):([^:>]+)(?::([-\d.]+))?(?::([-\d.]+))?>"

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
    def active(self):
        return self._active
    
    @pyqtSlot(int)
    def addNetwork(self, index):
        if index >= 0 and index < len(self._availableNetworks):
            net = self.availableNetworks[index]
            if net in self._activeNetworks:
                return
            
            name = self.gui.modelName(net)
            type = self.gui.netType(net)
            if type:
                type = {"LoRA":"lora", "HN":"hypernet"}[type]
            else:
                return
            
            self._values.set("prompt", self._values.get("prompt") + f"<{type}:{name}:1.0>")   

    @pyqtSlot(int)
    def deleteNetwork(self, index):
        net = self._activeNetworks[index]
        name = self.gui.modelName(net)
        type = self.gui.netType(net)
        if type:
            type = {"LoRA":"lora", "HN":"hypernet"}[type]
        else:
            return

        netre = fr"(?:\s)?<@?({type}):({name})(?::([-\d.]+))?(?::([-\d.]+))?>"
        positive = re.sub(netre,'',self._values.get("prompt"))
        negative = re.sub(netre,'',self._values.get("negative_prompt"))

        self._values.set("prompt", positive)
        self._values.set("negative_prompt", negative)
    
    @pyqtProperty(VariantMap, notify=updated)
    def values(self):
        return self._values

    @pyqtSlot(str, 'QVariant', 'QVariant')
    def mapsUpdating(self, key, prev, curr):
        pairs = [("true_sampler", "hr_sampler"), ("eta", "hr_eta"), ("steps", "hr_steps")]
        for src, dst in pairs:
            if key == src:
                val = self._values.get(dst)
                if val == prev:
                    self._values.set(dst, curr)

        self.updated.emit()

    @pyqtSlot(str)
    def onUpdated(self, key):
        self.getActive()
        self.updated.emit()

        if key != "sampler" and key != "schedule":
            return

        if key == "sampler":
            sampler = self._values.get("sampler")
            if sampler in {"DPM++ 2M", "DPM++ 2S a", "DPM++ SDE"}:
                self._values.set("schedules", ["Default", "Karras"])
            else:
                self._values.set("schedules", ["Default"])
            schedule = self._values.get("schedule")
            if not schedule in self._values.get("schedules"):
                self._values.set("schedule", "Default")

        true_sampler = self._values.get("sampler")
        schedule = self._values.get("schedule")
        if schedule and schedule != "Default":
            true_sampler += " " + schedule
        self._values.set("true_sampler", true_sampler)
        

    @pyqtSlot()
    def optionsUpdated(self):
        for k in self.gui._options:
            kk = k + "s"
            if kk in self._values._map:
                self._values.set(kk, self.gui._options[k])
            if not self._values.get(k) or not self._values.get(k) in self.gui._options[k]:
                if self.gui._options[k]:
                    self._values.set(k, self.gui._options[k][0])
                else:
                    self._values.set(k, "")
        models = []
        for k in self.gui._options["UNET"]:
            if k in self.gui._options["CLIP"] and k in self.gui._options["VAE"]:
                models += [k]
        self._values.set("models", models)
        if models and (not self._values.get("model") or not self._values.get("model") in models):
            self._values.set("model", models[0])

        unets = self._values.get("UNETs")
        unets = [u for u in unets if not u in models] + [u for u in unets if u in models]
        self._values.set("UNETs", unets)

        vaes = self._values.get("VAEs")
        vaes = [v for v in vaes if not v in models] + [v for v in vaes if v in models]
        self._values.set("VAEs", vaes)

        clips = self._values.get("CLIPs")
        clips = [c for c in clips if not c in models] + [c for c in clips if c in models]
        self._values.set("CLIPs", clips)

        self._availableNetworks = self._values.get("LoRAs") + self._values.get("HNs")
        self._activeNetworks = [n for n in self._activeNetworks if n in self._availableNetworks]

        if self._values.get("img2img_upscaler") not in self._values.get("img2img_upscalers"):
            self._values.set("img2img_upscaler", "Lanczos")

        if self._values.get("hr_upscaler") not in self._values.get("hr_upscalers"):
            self._values.set("hr_upscaler", "Latent (nearest)")

        pref_device = self.gui.config.get("device")
        if pref_device and pref_device in self._values.get("devices"):
            self._values.set("device", pref_device)

        pref_artifacts = self.gui.config.get("artifacts")
        if pref_artifacts and pref_artifacts in self._values.get("artifact_modes"):
            self._values.set("artifact_mode", pref_artifacts)

        pref_previews = self.gui.config.get("previews")
        if pref_previews and pref_previews in self._values.get("preview_modes"):
            self._values.set("preview_mode", pref_previews)

        pref_preview_interval = self.gui.config.get("preview_interval")
        if pref_preview_interval and pref_preview_interval >= 0:
            self._values.set("preview_interval", pref_preview_interval)

        pref_vram = self.gui.config.get("vram")
        if pref_vram and pref_vram in self._values.get("vram_modes"):
            self._values.set("vram_mode", pref_vram)

        self._values.set("true_samplers", self._values.get("samplers"))
        self._values.set("samplers", [s for s in self._values.get("samplers") if not "Karras" in s])

        mode_names = ["canny","depth","pose","lineart","softedge","anime","mlsd"]
        modes = []
        for m in mode_names:
            for cn in self._values.get("CNs"):
                if not m in modes and m in cn.rsplit(os.path.sep, 1)[-1]:
                    modes += [m.capitalize()]
        self._values.set("CN_modes", modes)
        
        self.updated.emit()

    def buildPrompts(self, batch_size):
        pos = self.parsePrompt(self._values._map['prompt'], batch_size)
        neg = self.parsePrompt(self._values._map['negative_prompt'], batch_size)
        return list(zip(pos, neg))

    def buildRequest(self, images=[], masks=[], areas=[], control=[]):
        request = {}
        data = {}

        for k, v in self._values._map.items():
            if not k in self._client_only:
                data[k] = v

        batch_size = int(data['batch_size'])
        batch_size = max(batch_size, len(images), len(masks), len(areas))

        data['prompt'] = self.buildPrompts(batch_size)

        data["sampler"] = data["true_sampler"]
        del data["true_sampler"]

        if data["steps"] == 0 and images:
            request["type"] = "upscale"
            data["image"] = images
            if masks:
                data["mask"] = masks
        elif images:
            request["type"] = "img2img"
            data["image"] = images
            if masks:
                data["mask"] = masks
        else:
            request["type"] = "txt2img"
            del data["mask_blur"]

        if areas:
            s = len(self.subprompts)
            for a in range(len(areas)):
                if len(areas[a]) > s:
                    areas[a] = areas[a][:s]
            data["area"] = areas

        if len({data["UNET"], data["CLIP"], data["VAE"]}) == 1:
            data["model"] = data["UNET"]
            del data["UNET"]
            del data["CLIP"]
            del data["VAE"]
        else:
            del data["model"]

        if data["hr_factor"] == 1.0:
            del data["hr_factor"]
            del data["hr_strength"]
            del data["hr_upscaler"]
            del data["hr_steps"]
            del data["hr_sampler"]
            del data["hr_eta"]
        else:
            if data["hr_steps"] == data["steps"]:
                del data["hr_steps"]
            if data["hr_eta"] == data["eta"]:
                del data["hr_eta"]
            if data["hr_sampler"] == data["sampler"]:
                del data["hr_sampler"]
        
        if not request["type"] in {"img2img", "upscale"}:
            del data["img2img_upscaler"]
        
        if data["eta"] == 1.0:
            del data["eta"]

        if data["padding"] == -1:
            del data["padding"]
        
        if data["subseed_strength"] != 0.0:
            data["subseed"] = (data["subseed"], data["subseed_strength"])
        else:
            del data["subseed"]
        del data["subseed_strength"]

        data["device_name"] = self._values._map["device"]

        if control:
            images = [i for m,i in control]
            modes = [m.lower() for m,i in control]
            models = []
            for m in modes:
                for cn in self._values.get("CNs"):
                    if m in cn.rsplit(os.path.sep, 1)[-1]:
                        models += [cn]
                        break
            data["cn_image"] = images
            data["cn"] = models
            data["cn_annotator"] = modes
            data["cn_args"] = [()] * len(modes)
            data["cn_scale"] = [data["cn_strength"]] * len(control)
        else:
            del data["cn_strength"]

        if request["type"] != "img2img" and "strength" in data:
            del data["strength"]

        if data["vram_mode"] == "Minimal":
            data["minimal_vram"] = True
        del data["vram_mode"]

        if data["artifact_mode"] == "Enabled":
            data["keep_artifacts"] = True
        del data["artifact_mode"]

        if data["preview_mode"] != "Disabled":
            data["show_preview"] = data["preview_mode"]
        del data["preview_mode"]

        if request["type"] == "upscale":
            for k in list(data.keys()):
                if not k in {"img2img_upscaler", "width", "height", "image", "mask", "mask_blur", "padding"}:
                    del data[k]

        data = {k.lower():v for k,v in data.items()}

        request["data"] = data

        return request

    def buildAnnotateRequest(self, mode, image):
        mode = mode.lower()
        data = {}
        args = []
        if mode == "canny":
            args = [100,200]
        data["cn_image"] = [image]
        data["cn_annotator"] = [mode.lower()]
        data["cn_args"] = [args]
        return {"type":"annotate", "data": data}

    @pyqtSlot()
    def reset(self):
        pass

    @pyqtSlot(list)
    def sync(self, params):
        hr_resize = None
        schedule = None

        found = {'hr_resize':False, 'hr_factor': False, 'hr_sampler': False, 'hr_steps': False, 'hr_eta': False,
              'sampler': False, 'steps': False, 'eta': False, 'model':False, 'VAE':False, "UNET":False, "CLIP":False}
        
        for p in params:
            if not p._checked:
                continue
            
            if p._name == "size":
                w,h = p._value.split("x")
                w,h = int(w), int(h)
                self.values.set("width", w)
                self.values.set("height", h)
                continue

            if p._name == "hr_resize":
                w,h = p._value.split("x")
                hr_resize = int(w), int(h)
                continue
                
            if p._name == "sampler":
                if p._value.endswith(" Karras"):
                    p._value = p._value.rsplit(" ",1)[0]
                    schedule = "Karras"
                else:
                    schedule = "Default"
                
            if p._name in found:
                found[p._name] = True

            if not p._name in self._values._map:
                continue 

            if p._name+"s" in self._values._map and not p._value in self._values._map[p._name+"s"]:
                for m in self._values._map[p._name+"s"]:
                    if p._value + "." in m:
                        p._value = m
                        break
                else:
                    continue

            val = None
            try:
                val = type(self.values.get(p._name))(p._value)
            except:
                pass

            if val:
                self.values.set(p._name, p._value)

        if schedule:
            self.values.set("schedule", schedule)

        if hr_resize:
            w,h = hr_resize
            w,h = w/self.values.get("width"), h/self.values.get("height")
            f = ((w+h)/2)
            f = int(f / 0.005) * 0.005
            self.values.set("hr_factor", f)

        if found["hr_factor"] or found["hr_resize"]:
            if not found["hr_steps"] and found["steps"]:
                self.values.set("hr_steps", self.values.get("steps"))
            if not found["hr_sampler"] and found["sampler"]:
                self.values.set("hr_sampler", self.values.get("sampler"))
            if not found["hr_eta"] and found["eta"]:
                self.values.set("hr_eta", self.values.get("eta"))

        if found["UNET"] and found["VAE"] and found["CLIP"]:
            self.values.set("model", self.values.get("UNET"))
        elif found["model"]:
            model = self.values.get("model")
            self.values.set("UNET", model)
            self.values.set("VAE", model)
            self.values.set("CLIP", model)
        
        self.updated.emit()
        pass

    def parsePrompt(self, prompt, batch_size):
        wildcards = self.gui.wildcards._wildcards
        counter = self.gui.wildcards._counter
        prompts = []
        pattern = re.compile("@?__([^\s]+?)__(?!___)")
        for i in range(batch_size):
            sp = self.parseSubprompts(str(prompt))
            for j in range(len(sp)):
                p = sp[j]
                while m := pattern.search(p):
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
                            c = random.SystemRandom().choice(wildcards[name])
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
        self._active = []

        prompt = self._values.get("prompt") + " " + self._values.get("negative_prompt")

        for lora_match in re.findall(r"<@?lora:([^:>]+)([^>]+)?>", prompt):
            for lora in self._values.get("LoRAs"):
                if lora_match[0] + "." in lora:
                    self._active += [lora]

        for hn_match in re.findall(r"<@?hypernet:([^:>]+)([^>]+)?>", prompt):
            for hn in self._values.get("HNs"):
                if hn_match[0] + "." in hn:
                    self._active += [hn]

        for w_match in re.findall(r"@?__([^\s]+?)__(?!___)", prompt):
            if w_match in self.gui.wildcards._wildcards:
                self._active += [os.path.join("WILDCARD", w_match + ".txt")]

        for emb in self._values.get("TIs"):
            if self.gui.modelName(emb) in prompt:
                self._active += [emb]

        for model in [self._values.get(m) for m in ["UNET", "VAE", "CLIP"]]:
            if model and "." in model and not model in self._active:
                self._active += [model]

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

        if file in self._values.get("HNs"):
            append(f"<hypernet:{name}>")

        if file in self._values.get("TIs"):
            if "neg" in re.split(r'/|\\', file, 1)[0].lower():
                append(name, "negative_prompt")
            else:
                append(name)

        if file.startswith("WILDCARD") and name in self.gui.wildcards._wildcards:
            append(f"__{name}__")
        
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
            remove(fr"<@?lora:({name})(?::([-\d.]+))?(?::([-\d.]+))?>")

        if file in self._values.get("HNs"):
            remove(fr"<@?hypernet:({name})(?::([-\d.]+))?(?::([-\d.]+))?>")

        if file in self._values.get("TIs"):
            remove(fr"{name}")

        if file.startswith("WILDCARD") and name in self.gui.wildcards._wildcards:
            remove(fr"__{name}__")

    @pyqtSlot(str)
    def doToggle(self, file):
        if file in self._active:
            self.doDeactivate(file)
        else:
            self.doActivate(file)
        
def registerTypes():
    qmlRegisterUncreatableType(Parameters, "gui", 1, 0, "ParametersMap", "Not a QML type")
    qmlRegisterUncreatableType(VariantMap, "gui", 1, 0, "VariantMap", "Not a QML type")
    qmlRegisterUncreatableType(ParametersItem, "gui", 1, 0, "ParametersItem", "Not a QML type")
    qmlRegisterType(ParametersParser, "gui", 1, 0, "ParametersParser")