from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QVariant
from PyQt5.QtQml import qmlRegisterUncreatableType

class VariantMap(QObject):
    updated = pyqtSignal()
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
        self.updated.emit()
    

class Parameters(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent

        self.gui.optionsUpdated.connect(self.optionsUpdated)

        self._readonly = ["models", "samplers", "upscalers", "UNETs", "CLIPs", "VAEs", "SRs", "LoRAs", "HNs"]
        self._values = VariantMap(self, {"width": 512, "height": 512, "steps": 25, "scale": 7, "strength": 0.75, "seed": -1, "eta": 0.0,
            "model":"", "models":[], "sampler":"", "samplers":[], "upscaler":"", "upscalers":[],
            "UNET":"", "UNETs":"", "CLIP":"", "CLIPs":[], "VAE":"", "VAEs":[], "SR":"", "SRs":[], "LoRA":"", "LoRAs":[], "HN":"", "HNs":[]})
        self._values.updated.connect(self.mapsUpdated)

    @pyqtProperty(VariantMap, notify=updated)
    def defaults(self):
        return self._defaults
    
    @pyqtProperty(VariantMap, notify=updated)
    def values(self):
        return self._values

    @pyqtSlot()
    def mapsUpdated(self):
        self.updated.emit()

    @pyqtSlot()
    def optionsUpdated(self):
        for k in self.gui._options:
            kk = k + "s"
            if kk in self._values._map:
                self._values.set(kk, self.gui._options[k])
            if not self._values.get(k) in self.gui._options[k]:
                if self.gui._options[k]:
                    self._values.set(k, self.gui._options[k][0])
                else:
                    self._values.set(k, "")

        models = []
        for k in self.gui._options["UNET"]:
            if k in self.gui._options["CLIP"] and k in self.gui._options["VAE"]:
                models += [k]
        self._values.set("models", models)
        if models:
            self._values.set("model", models[0])
        else:
            self._values.set("model", "")
         
        self.updated.emit()

    @pyqtSlot()
    def reset(self):
        pass
        
def registerTypes():
    qmlRegisterUncreatableType(Parameters, "gui", 1, 0, "ParametersMap", "Not a QML type")
    qmlRegisterUncreatableType(VariantMap, "gui", 1, 0, "VariantMap", "Not a QML type")