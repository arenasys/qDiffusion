import PIL.Image
import shutil
import os
import send2trash
import glob

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QUrl, QMimeData
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication
import sql
import filesystem
import parameters

class Populater(QObject):
    stop = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.paths = []

        self.conn = None
        self.watcher = filesystem.Watcher.instance
        self.folders = set()

    @pyqtSlot()
    def started(self):
        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE folders(folder TEXT UNIQUE, name TEXT UNIQUE);")
        self.conn.doQuery("CREATE TABLE images(file TEXT UNIQUE, folder TEXT, parameters TEXT, idx INTEGER, width INTEGER, height INTEGER, CONSTRAINT unq UNIQUE (folder, idx));")
        self.conn.enableNotifications("folder")
        self.conn.enableNotifications("images")

        self.watcher.finished.connect(self.onFinished)
        self.watcher.folder_changed.connect(self.onResult)
        
    @pyqtSlot(str, str)
    def addFolder(self, name, folder):
        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT OR REPLACE INTO folders(folder, name) VALUES (:folder, :name);")
        q.bindValue(":folder", folder)
        q.bindValue(":name", name)
        self.conn.doQuery(q)

        self.folders.add(folder)
        self.watcher.watchFolder(folder)

    @pyqtSlot(str, int)
    def onFinished(self, folder, total):
        if not folder in self.folders:
            return
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM images WHERE folder == :folder AND idx >= :total;")
        q.bindValue(":folder", folder)
        q.bindValue(":total", total)
        self.conn.doQuery(q)

        self.conn.enableNotifications("images")

    @pyqtSlot(str, str, int)
    def onResult(self, folder, file, idx):
        if not folder in self.folders:
            return
        
        ext = file.split(".")[-1]
        if not ext in {"png"}:
            return
        
        parameters = ""
        try:
            with PIL.Image.open(file) as img:
                if "parameters" in img.info:
                    parameters = img.info["parameters"]
                width, height = img.size
        except Exception:
            return
        
        if idx == 0:
            self.conn.disableNotifications("images")
        if idx % 1000 == 999:
            self.conn.relayNotification("images")

        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT OR REPLACE INTO images(file, folder, parameters, idx, width, height) VALUES (:file, :folder, :parameters, :idx, :width, :height);")
        q.bindValue(":file", file)
        q.bindValue(":folder", folder)
        q.bindValue(":parameters", parameters)
        q.bindValue(":idx", idx)
        q.bindValue(":width", width)
        q.bindValue(":height", height)
        self.conn.doQuery(q)

class Deleter(QThread):
    def __init__(self, gui, files):
        super().__init__()
        self.files = files
        self.gui = gui
    def run(self):
        send2trash.send2trash(self.files)
        self.gui.thumbnails.removeAll(self.files)

class Gallery(QObject):
    add_folder = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 3
        self.name = "Gallery"

        qmlRegisterSingletonType(Gallery, "gui", 1, 0, "GALLERY", lambda qml, js: self)

        self.populater = Populater()
        self.add_folder.connect(self.populater.addFolder)

        self.populaterThread = QThread()
        self.populaterThread.started.connect(self.populater.started)

        self.populater.moveToThread(self.populaterThread)
        self.populaterThread.start()

        output = self.gui.outputDirectory()
        order = ["txt2img", "img2img", "favourites"]
        labels = {"txt2img": "Txt2Img", "img2img": "Img2Img"}

        for s in order:
            os.makedirs(os.path.join(output, s), exist_ok=True)

        subfolders = [s.rsplit(os.path.sep,1)[-1] for s in list(filter(os.path.isdir, glob.glob(output + "/*")))]
        subfolders = [o for o in order if o in subfolders] + [s for s in subfolders if not s in order]
        for name in subfolders:
            label = name.capitalize()
            if name in labels:
                label = labels[name]
            self.add_folder.emit(label, os.path.join(output, name))

        parent.aboutToQuit.connect(self.stop)

        self.deleters = []

    @pyqtSlot(list)
    def doOpenImage(self, files):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(files[0])))

    @pyqtSlot(list)
    def doOpenFolder(self, files):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(os.path.abspath(files[0]))))

    @pyqtSlot(str, list)
    def doCopy(self, folder, files):
        idx = parameters.get_index(folder)
        for src in files:
            dst = os.path.join(folder, f"{idx:07d}.png")
            shutil.copy(src, dst)
            idx += 1

    @pyqtSlot(str, list)
    def doMove(self, folder, files):
        idx = parameters.get_index(folder)
        for src in files:
            dst = os.path.join(folder, f"{idx:07d}.png")
            shutil.move(src, dst)
            idx += 1

    @pyqtSlot(list)
    def doDelete(self, files):
        deleter = Deleter(self.gui, files)
        deleter.start()
        self.deleters += [deleter]

    @pyqtSlot(list)
    def doClipboard(self, files):
        self.gui.copyFiles(files)

    @pyqtSlot(list)
    def doDrag(self, files):
        self.gui.dragFiles(files)

    @pyqtSlot()
    def stop(self):
        self.populaterThread.quit()
        self.populaterThread.wait()