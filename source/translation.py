from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QUrl
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType

import json
import os
import glob

class TranslatorInstance(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.translator = parent
    
    @pyqtSlot(str, str, result=str)
    def translate(self, str, file):
        return self.translator.translate(str, file)

class Translator(QObject):
    updated = pyqtSignal()
    languagesUpdated = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self.gui = parent
        self._instance = TranslatorInstance(self)
        self._writing = True

        self._language = "English"
        self._languages = {}
        self.loadLanguages()

        self._capture = None
        try:
            if os.path.exists("capture.json"):
                self._capture = {}
                with open("capture.json", 'r', encoding="utf-8") as f:
                    self._capture = json.load(f)
        except Exception:
            pass

        qmlRegisterUncreatableType(TranslatorInstance, "gui", 1, 0, "TranslationInstance", "Not a QML type")
        qmlRegisterSingletonType(Translator, "gui", 1, 0, "TRANSLATOR", lambda qml, js: self)

    @pyqtSlot()
    def loadLanguages(self):
        self._languages = {}
        for file in glob.glob(os.path.join("source", "languages", "*.json")):
            try:
                name = file.rsplit(os.path.sep, 1)[-1].split(".", 1)[0]
                with open(file, 'r', encoding="utf-8") as f:
                    self._languages[name] = json.load(f)
            except Exception:
                pass
        self.languagesUpdated.emit()

    @pyqtSlot()
    def addLanguageContent(self, name, content):
        if not name in self._languages:
            return
        
        for file in content:
            if not file in self._languages:
                self._languages[file] = content[file]
            else:
                for k in content[file]:
                    if not k in self._languages[file]:
                        self._languages[file][k] = content[file][k]
        
        if self._language == name:
            self.updated.emit()
    
    @pyqtProperty(TranslatorInstance, notify=updated)
    def instance(self):
        return self._instance
    
    @pyqtProperty(list, notify=languagesUpdated)
    def languages(self):
        return sorted(list(self._languages.keys()))

    @pyqtProperty(str, notify=updated)
    def language(self):
        return self._language
    
    @language.setter
    def language(self, language):
        if language in self._languages:
            self._language = language
            self.updated.emit()

    def captureTranslation(self, str, file):
        if self._capture == None:
            return
        modified = False
        if not file in self._capture:
            self._capture[file] = {}
            modified = True
        if not str in self._capture[file] and str:
            self._capture[file][str] = ""
            modified = True
        if modified:
            t = self._capture
            ordered = {f:{k:t[f][k] for k in sorted(t[f].keys())} for f in sorted(t.keys())}
            try:
                with open("capture.json", 'w', encoding="utf-8") as f:
                    json.dump(ordered, f, indent=4)
            except Exception:
                pass

    @pyqtSlot(str, str, result=str)
    def translate(self, str, file):
        self.captureTranslation(str, file)

        if not self._language in self._languages:
            return str
        
        language = self._languages[self._language]
        if file in language and str in language[file] and language[file][str]:
            return language[file][str]

        return str