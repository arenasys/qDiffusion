import io
import os
import re

import PIL.Image
import PIL.PngImagePlugin

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QVariant
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
    ("hr_upscaler", "Hires upscaler")
]
NETWORKS = {"LoRA":"lora","HN":"hypernet"}
NETWORKS_INV = {"lora":"LoRA","hypernet":"HN"}

def format_parameters(json):
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

def save_image(img, metadata):
    global IDX
    if type(img) == bytes:
        img = PIL.Image.open(io.BytesIO(img))
    m = PIL.PngImagePlugin.PngInfo()
    m.add_text("parameters", format_parameters(metadata))

    folder = os.path.join("outputs", metadata["mode"])
    os.makedirs(folder, exist_ok=True)

    def get_idx(filename):
        try:
            return int(filename.split(".")[0])
        except Exception:
            return 0

    if IDX == -1:
        IDX = max([get_idx(f) for f in os.listdir(folder)] + [0]) + 1
    else:
        IDX += 1
    
    idx = IDX

    while os.path.exists(os.path.join(folder, f"{idx:07d}.png")):
        idx += 1

    tmp = os.path.join(folder, f"{idx:07d}.tmp")
    real = os.path.join(folder, f"{idx:07d}.png")

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
        h = w/ar
        if h > src_h:
            h = src_h
            w = h*ar
    else:
        h = rh
        w = int(h*ar)
        if w > src_w:
            w = src_w
            h = w/ar

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
        if key in self._map:
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

class ParametersNetwork(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, name="", type=""):
        super().__init__(parent)
        self._name = name
        self._type = type

    @pyqtProperty(str, notify=updated)
    def name(self):
        return self._name
    
    @pyqtProperty(str, notify=updated)
    def type(self):
        return self._type
    
class Parameters(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent

        self.gui.optionsUpdated.connect(self.optionsUpdated)

        self._readonly = ["models", "samplers", "upscalers", "UNETs", "CLIPs", "VAEs", "SRs", "LoRAs", "HNs", "hr_upscalers", "img2img_upscalers"]
        self._values = VariantMap(self, {"prompt":"", "negative_prompt":"", "width": 512, "height": 512, "steps": 25, "scale": 7, "strength": 0.75, "seed": -1, "eta": 1.0,
            "hr_factor": 1.0, "hr_strength":  0.7, "clip_skip": 2, "batch_size": 1, "padding": -1, "mask_blur": 4, "subseed":-1, "subseed_strength": 0.0,
            "model":"", "models":[], "sampler":"Euler a", "samplers":[], "hr_upscaler":"Latent (nearest)", "hr_upscalers":[], "img2img_upscaler":"Lanczos", "img2img_upscalers":[], "upscalers":[],
            "UNET":"", "UNETs":"", "CLIP":"", "CLIPs":[], "VAE":"", "VAEs":[], "SR":"", "SRs":[], "LoRA":[], "LoRAs":[], "HN":[], "HNs":[]})
        self._values.updated.connect(self.mapsUpdated)
        self._availableNetworks = []
        self._activeNetworks = []

    @pyqtSlot()
    def promptsChanged(self):
        positive = self._values.get("prompt")
        negative = self._values.get("negative_prompt")

        netre = r"<(lora|hypernet):([^:>]+)(?::([-\d.]+))?(?::([-\d.]+))?>"

        nets = re.findall(netre, positive) + re.findall(netre, negative)
        self._activeNetworks = [ParametersNetwork(self, net[1], NETWORKS_INV[net[0]]) for net in nets]
        self.updated.emit()

    @pyqtProperty(list, notify=updated)
    def availableNetworks(self):
        return self._availableNetworks

    @pyqtProperty(list, notify=updated)
    def activeNetworks(self):
        return self._activeNetworks
    
    @pyqtSlot(int)
    def addNetwork(self, index):
        if index >= 0 and index < len(self._availableNetworks):
            net = self.availableNetworks[index]
            if any([n._name == net.name and n._type == net.type for n in self._activeNetworks]):
                return
            
            self._values.set("prompt", self._values.get("prompt") + f"<{NETWORKS[net._type]}:{net.name}:1.0>")   

    @pyqtSlot(int)
    def deleteNetwork(self, index):
        net = self._activeNetworks[index]
        t = NETWORKS[net._type]
        netre = fr"(?:\s)?<({t}):({net._name})(?::([-\d.]+))?(?::([-\d.]+))?>"
        positive = re.sub(netre,'',self._values.get("prompt"))
        negative = re.sub(netre,'',self._values.get("negative_prompt"))

        self._values.set("prompt", positive)
        self._values.set("negative_prompt", negative)
    
    @pyqtProperty(VariantMap, notify=updated)
    def values(self):
        return self._values

    @pyqtSlot(str)
    def mapsUpdated(self, key):
        if key == "model":
            model = self._values.get("model")
            self._values.set("UNET", model)
            self._values.set("CLIP", model)
            self._values.set("VAE", model)
        
        self.updated.emit()

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

        self._availableNetworks = [ParametersNetwork(self, name, "LoRA") for name in self._values.get("LoRAs")]
        self._availableNetworks += [ParametersNetwork(self, name, "HN") for name in self._values.get("HNs")]
        self._activeNetworks = [n for n in self._activeNetworks if any([n == nn._name for nn in self._availableNetworks])]

        upscalers = self._values.get("upscalers") + self._values.get("SRs")

        self._values.set("img2img_upscalers", [u for u in upscalers if not u.startswith("Latent ")])
        if self._values.get("img2img_upscaler") not in self._values.get("img2img_upscalers"):
            self._values.set("img2img_upscaler", "Lanczos")

        self._values.set("hr_upscalers", upscalers)
        if self._values.get("hr_upscaler") not in self._values.get("hr_upscalers"):
            self._values.set("hr_upscaler", "Latent (nearest)")
         
        self.updated.emit()

    def buildRequest(self, images=[], masks=[]):
        request = {}
        data = {}

        if images:
            request["type"] = "img2img"     
            data["image"] = images
            data["mask"] = masks           
        else:
            request["type"] = "txt2img"

        for k, v in self._values._map.items():
            if not k in self._readonly:
                data[k] = v
        del data["SR"]

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

        if request["type"] != "img2img":
            del data["strength"]
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

        data = {k.lower():v for k,v in data.items()}

        request["data"] = data

        return request

    @pyqtSlot()
    def reset(self):
        pass

    @pyqtSlot(list)
    def sync(self, params):
        hr_resize = None

        lora = []
        lora_str = []

        hn = []
        hn_str = []

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

            if not p._name in self._values._map:
                continue

            if p._name+"s" in self._values._map and not p._value in self._values._map[p._name+"s"]:
                continue

            self.values.set(p._name, type(self.values.get(p._name))(p._value))

        if hr_resize:
            w,h = hr_resize
            w,h = w/self.values.get("width"), h/self.values.get("height")
            f = ((w+h)/2)
            f = int(f / 0.005) * 0.005
            self.values.set("hr_factor", f)

        if lora or hn:
            self._activeNetworks = []
        
        for i in range(len(lora)):
            str = 1.0
            if i < len(lora_str):
                str = float(lora_str[i])
            self._activeNetworks += [ParametersNetwork(self, lora[i], "LoRA", str)]
        
        for i in range(len(hn)):
            str = 1.0
            if i < len(hn_str):
                str = float(hn_str[i])
            self._activeNetworks += [ParametersNetwork(self, hn[i], "HN", str)]

        self.updated.emit()

        pass
        
def registerTypes():
    qmlRegisterUncreatableType(Parameters, "gui", 1, 0, "ParametersMap", "Not a QML type")
    qmlRegisterUncreatableType(VariantMap, "gui", 1, 0, "VariantMap", "Not a QML type")
    qmlRegisterUncreatableType(ParametersItem, "gui", 1, 0, "ParametersItem", "Not a QML type")
    qmlRegisterType(ParametersParser, "gui", 1, 0, "ParametersParser")