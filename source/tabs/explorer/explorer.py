from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QImage, QDesktopServices

import sql
import os
import PIL.Image
import misc
import re
import shutil

class Explorer(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 1
        self.name = "Models"
        self.gui = parent

        qmlRegisterSingletonType(Explorer, "gui", 1, 0, "EXPLORER", lambda qml, js: self)

        self.gui.optionsUpdated.connect(self.optionsUpdated)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE models(name TEXT, category TEXT, type TEXT, file TEXT, folder TEXT, desc TEXT, idx INTEGER, width INTEGER, height INTEGER, CONSTRAINT unq UNIQUE (category, idx));")
        self.conn.enableNotifications("models")

    def setModel(self, name, category, type, idx):
        q = QSqlQuery(self.conn.db)

        file =  os.path.abspath(os.path.join(self.gui.modelDirectory(), name.rsplit(".",1)[0]))
        folder = ""
        parts = re.split(r'/|\\', name)
        if len(parts) > 2:
            folder = parts[1]
        
        preview = file + ".png"
        desc = file + ".txt"

        w,h = 0,0
        if os.path.exists(preview):
            try:
                with PIL.Image.open(preview) as img:
                    w,h = img.size
            except:
                pass
        
        description = ""
        if os.path.exists(desc):
            with open(desc, "r", encoding='utf-8') as f:
                description = f.read().strip()
        
        q.prepare("INSERT OR REPLACE INTO models(name, category, type, file, folder, desc, idx, width, height) VALUES (:name, :category, :type, :file, :folder, :desc, :idx, :width, :height);")
        q.bindValue(":name", name)
        q.bindValue(":category", category)
        q.bindValue(":type", type)
        q.bindValue(":file", preview)
        q.bindValue(":folder", folder)
        q.bindValue(":desc", description)
        q.bindValue(":idx", idx)
        q.bindValue(":width", w)
        q.bindValue(":height", h)
        self.conn.doQuery(q)

    def finishCategory(self, category, total):
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM models WHERE category == :category AND idx >= :total;")
        q.bindValue(":category", category)
        q.bindValue(":total", total)
        self.conn.doQuery(q)

    @pyqtSlot()
    def optionsUpdated(self):
        o = self.gui._options

        checkpoints = [a for a in o["UNET"] if a in o["VAE"] and a in o["CLIP"]]
        for idx, name in enumerate(checkpoints):
            self.setModel(name, "checkpoint", "", idx)
        self.finishCategory("checkpoint", len(checkpoints))
        
        components = [a for a in o["VAE"] if not a in checkpoints]
        for idx, name in enumerate(components):
            self.setModel(name, "component", "VAE", idx)
        self.finishCategory("component", len(components))

        for idx, name in enumerate(o["LoRA"]):
            self.setModel(name, "lora", "", idx)
        self.finishCategory("lora", len(o["LoRA"]))
        
        for idx, name in enumerate(o["HN"]):
            self.setModel(name, "hypernet", "", idx)
        self.finishCategory("hypernet", len(o["HN"]))

        for idx, name in enumerate(o["TI"]):
            self.setModel(name, "embedding", "", idx)
        self.finishCategory("embedding", len(o["TI"]))

        for idx, name in enumerate(self.gui.wildcards._wildcards):
            self.setModel(os.path.join("WILDCARD", name + ".txt"), "wildcard", "", idx)
        self.finishCategory("wildcard", len(self.gui.wildcards._wildcards))

    @pyqtSlot(misc.MimeData, str)
    def doReplace(self, mimedata, file):
        mimedata = mimedata.mimeData
        image = None
        if mimedata.hasImage():
            image = mimedata.imageData()
            if image and not image.isNull():
                image.save(file)

        for url in mimedata.urls():
            if url.isLocalFile():
                image = QImage(url.toLocalFile())
                break
        
        if image:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            image.save(file)
            self.gui.thumbnails.remove(file)
            self.gui.watchModelDirectory()
            
    @pyqtSlot(str)
    def doClear(self, file):
        if os.path.exists(file):
            os.remove(file)
            self.gui.thumbnails.remove(file)

    @pyqtSlot(str)
    def doDelete(self, file):
        request = {"type":"manage", "data": {"operation": "modify", "old_file": file, "new_file": ""}}
        self.gui.makeRequest(request)

    @pyqtSlot(str)
    def doVisit(self, file):
        path = os.path.abspath(os.path.join(self.gui.modelDirectory(), os.path.dirname(file)))
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass

    @pyqtSlot(str, str, str)
    def doEdit(self, file, name, desc):
        old_file = file
        new_file = os.path.join(os.path.dirname(old_file), name)
        old_path = os.path.abspath(os.path.join(self.gui.modelDirectory(), old_file.split('.',1)[0]))
        new_path = os.path.abspath(os.path.join(self.gui.modelDirectory(), new_file.split('.',1)[0]))

        if old_file != new_file:
            if os.path.exists(old_path + ".txt"):
                shutil.move(old_path + ".txt", new_path + ".txt")
            if os.path.exists(old_path + ".png"):
                shutil.move(old_path + ".png", new_path + ".png")

        if desc:
            with open(new_path + ".txt", "w", encoding='utf-8') as f:
                f.write(desc)
        elif os.path.exists(new_path + ".txt"):
            os.remove(new_path + ".txt")

        if old_file != new_file:
            request = {"type":"manage", "data": {"operation": "modify", "old_file": old_file, "new_file": new_file}}
            self.gui.makeRequest(request)

        self.optionsUpdated()