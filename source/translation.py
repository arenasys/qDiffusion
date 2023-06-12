from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QUrl
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType

import json

class TranslatorInstance(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.translator = parent
    
    @pyqtSlot(str, str, result=str)
    def translate(self, str, file):
        return self.translator.translate(str, file)

class Translator(QObject):
    updated = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self.gui = parent
        self._instance = TranslatorInstance(self)
        self._writing = True

        self._translations = {}

        qmlRegisterUncreatableType(TranslatorInstance, "gui", 1, 0, "TranslationInstance", "Not a QML type")
        qmlRegisterSingletonType(Translator, "gui", 1, 0, "TRANSLATOR", lambda qml, js: self)

    @pyqtSlot()
    def write(self):
        t = self._translations
        ordered = {f:{k:t[f][k] for k in sorted(t[f].keys())} for f in sorted(t.keys())}
        try:
            with open("translations.json", 'w', encoding="utf-8") as f:
                json.dump(ordered, f, indent=4)
        except Exception:
            return

    def reload(self):
        self.updated.emit()
    
    @pyqtProperty(TranslatorInstance, notify=updated)
    def instance(self):
        return self._instance

    @pyqtSlot(str, str, result=str)
    def translate(self, str, file):
        if not file in self._translations:
            self._translations[file] = {}
        if not str in self._translations[file] and str:
            self._translations[file][str] = "" 
        #self.write()
        return str