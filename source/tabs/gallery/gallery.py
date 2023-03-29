import PIL.Image
import shutil
import os
import send2trash

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QUrl, QMimeData
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication
import sql
import filesystem

class Populater(QObject):
    stop = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.paths = []

        self.conn = sql.Connection(self)
        self.watcher = filesystem.Watcher.instance
        self.folders = set()

    @pyqtSlot()
    def started(self):
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

        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT OR REPLACE INTO images(file, folder, parameters, idx, width, height) VALUES (:file, :folder, :parameters, :idx, :width, :height);")
        q.bindValue(":file", file)
        q.bindValue(":folder", folder)
        q.bindValue(":parameters", parameters)
        q.bindValue(":idx", idx)
        q.bindValue(":width", width)
        q.bindValue(":height", height)
        self.conn.doQuery(q)
        
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

        self.add_folder.emit("Txt2Img", "outputs/txt2img")
        self.add_folder.emit("Img2Img", "outputs/img2img")
        self.add_folder.emit("Favourites", "outputs/favourites")

        parent.aboutToQuit.connect(self.stop)

    @pyqtSlot(list)
    def doOpenImage(self, files):
        QDesktopServices.openUrl(QUrl.fromLocalFile(files[0]))

    @pyqtSlot(list)
    def doOpenFolder(self, files):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(files[0])))

    @pyqtSlot(str, list)
    def doCopy(self, folder, files):
        for src in files:
            name = src.split(os.path.sep)[-1]
            dst = os.path.join(folder, name)
            shutil.copy(src, dst)

    @pyqtSlot(str, list)
    def doMove(self, folder, files):
        for src in files:
            name = src.split(os.path.sep)[-1]
            dst = os.path.join(folder, name)
            shutil.move(src, dst)

    @pyqtSlot(list)
    def doDelete(self, files):
        for f in files:
            send2trash.send2trash(f)
        self.gui.thumbnails.removeAll(files)

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