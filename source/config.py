import json

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread

from parameters import VariantMap

class Config(QObject):
    updated = pyqtSignal()
    def __init__(self, parent, file, defaults):
        super().__init__(parent)
        self._file = file
        self._defaults = defaults
        self._values = VariantMap(self, defaults.copy())
        self.loadConfig()

        self._values.updated.connect(self.saveConfig)

    @pyqtSlot()
    def loadConfig(self):
        data = {}
        try:
            with open(self._file, 'r', encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return
        for k, v in data.items():
            self._values.set(k,v)

    @pyqtSlot()
    def saveConfig(self):
        data = self._values._map
        data = {k:v for k,v in data.items() if not (k in self._defaults and str(self._defaults[k]) == str(v))}

        try:
            with open(self._file, 'w', encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            return
        self.updated.emit()