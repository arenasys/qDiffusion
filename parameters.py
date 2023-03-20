from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QVariant
from PyQt5.QtQml import qmlRegisterUncreatableType
    
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

class ParametersNetwork(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, name="", type=""):
        super().__init__(parent)
        self._name = name
        self._type = type
        self._strength = 1.0

    @pyqtProperty(str, notify=updated)
    def name(self):
        return self._name
    
    @pyqtProperty(str, notify=updated)
    def type(self):
        return self._type
    
    @pyqtProperty(float, notify=updated)
    def strength(self):
        return self._strength
    
    @strength.setter
    def strength(self, strength):
        self._strength = strength
        self.updated.emit()

class Parameters(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent

        self.gui.optionsUpdated.connect(self.optionsUpdated)

        self._readonly = ["models", "samplers", "upscalers", "UNETs", "CLIPs", "VAEs", "SRs", "LoRAs", "HNs"]
        self._values = VariantMap(self, {"width": 512, "height": 512, "steps": 25, "scale": 7, "strength": 0.75, "seed": -1, "eta": 0.0,
            "hr_factor": 1.0, "hr_strength":  0.7, "clip_skip": 2, "batch_size": 1,
            "model":"", "models":[], "sampler":"Euler a", "samplers":[], "hr_upscaler":"Latent (nearest)", "hr_upscalers":[], "img2img_upscaler":"Lanczos", "img2img_upscalers":[], "upscalers":[],
            "UNET":"", "UNETs":"", "CLIP":"", "CLIPs":[], "VAE":"", "VAEs":[], "SR":"", "SRs":[], "LoRA":[], "LoRAs":[], "HN":[], "HNs":[]})
        self._values.updated.connect(self.mapsUpdated)
        self._availableNetworks = []
        self._activeNetworks = []

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
            if any([n.name == net.name and n.type == net.type for n in self._activeNetworks]):
                return

            self._activeNetworks += [ParametersNetwork(self, net.name, net.type)]
            self.updated.emit()

    @pyqtSlot(int)
    def deleteNetwork(self, index):
        self._activeNetworks.pop(index)
        self.updated.emit()
    
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
        if models and not self._values.get("model") or not self._values.get("model") in models:
            self._values.set("model", models[0])

        self._availableNetworks = [ParametersNetwork(self, name, "LoRA") for name in self._values.get("LoRAs")]
        self._availableNetworks += [ParametersNetwork(self, name, "HN") for name in self._values.get("HNs")]
        self._activeNetworks = [n for n in self._activeNetworks if any([n == nn._name for nn in self._availableNetworks])]

        self._values.set("img2img_upscalers", [u for u in self._values.get("upscalers") if not u.startswith("Latent ")])
        if self._values.get("img2img_upscaler") not in self._values.get("img2img_upscalers"):
            self._values.set("img2img_upscaler", "Lanczos")

        self._values.set("hr_upscalers", self._values.get("upscalers"))
        if self._values.get("hr_upscaler") not in self._values.get("hr_upscalers"):
            self._values.set("hr_upscaler", "Latent (nearest)")
         
        self.updated.emit()

    @pyqtSlot()
    def reset(self):
        pass
        
def registerTypes():
    qmlRegisterUncreatableType(Parameters, "gui", 1, 0, "ParametersMap", "Not a QML type")
    qmlRegisterUncreatableType(VariantMap, "gui", 1, 0, "VariantMap", "Not a QML type")