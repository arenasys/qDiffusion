import glob
import os
import PIL.Image

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QThreadPool, QRunnable, QFileSystemWatcher
from PyQt5.QtSql import QSqlQuery

import sql
import filesystem

class PopulaterRunnableSignals(QObject):
    found = pyqtSignal(int, str, str, str)
    completed = pyqtSignal(str, int)
    def __init__(self, folder):
        super().__init__()
        self.stopping = False
        self.folder = folder

    @pyqtSlot(str)
    def stop(self, folder):
        if folder == self.folder:
            self.stopping = True

class PopulaterRunnable(QRunnable):
    found_image = pyqtSignal(int, str, str, str)
    def __init__(self, folder):
        super(PopulaterRunnable, self).__init__()
        self.signals = PopulaterRunnableSignals(folder)
        self.folder = folder
    
    @pyqtSlot()
    def run(self):
        try:
            files = glob.glob(os.path.join(self.folder, "*.png"))
            files = sorted(files, key = os.path.getmtime)
            for i, file in enumerate(files):
                with PIL.Image.open(file) as img:
                    params = img.info.get("parameters", "")
                if self.signals.stopping:
                    return
                self.signals.found.emit(i, file, self.folder, params)
            if not self.signals.stopping:
                self.signals.completed.emit(self.folder, len(files))
        except Exception:
            return

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
        self.conn.doQuery("CREATE TABLE images(file TEXT UNIQUE, folder TEXT, parameters TEXT);")
        self.conn.enableNotifications("folder")
        self.conn.enableNotifications("images")

        self.watcher.finished.connect(self.on_finished)
        self.watcher.result.connect(self.on_result)
        
    @pyqtSlot(str, str)
    def add_folder(self, name, folder):
        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT OR REPLACE INTO folders(folder, name) VALUES (:folder, :name);")
        q.bindValue(":folder", folder)
        q.bindValue(":name", name)
        self.conn.doQuery(q)

        self.folders.add(folder)
        self.watcher.watch_folder(folder)

    @pyqtSlot(str, int)
    def on_finished(self, folder, total):
        if not folder in self.folders:
            return
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM images WHERE folder == :folder AND rowid >= :total;")
        q.bindValue(":folder", folder)
        q.bindValue(":total", total)
        self.conn.doQuery(q)

    @pyqtSlot(str, str, int)
    def on_result(self, folder, file, idx):
        if not folder in self.folders:
            return
        
        ext = file.split(".")[-1]
        if not ext in {"png"}:
            return
        
        try:
            with PIL.Image.open(file) as img:
                parameters = img.info["parameters"]
        except Exception:
            return
            
        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT OR REPLACE INTO images(rowid, file, folder, parameters) VALUES (:idx, :file, :folder, :parameters);")
        q.bindValue(":idx", idx)
        q.bindValue(":file", file)
        q.bindValue(":folder", folder)
        q.bindValue(":parameters", parameters)
        self.conn.doQuery(q)
        
class gallery(QObject):
    add_folder = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 3
        self.name = "Gallery"

        self.populater = Populater()
        self.add_folder.connect(self.populater.add_folder)

        self.populaterThread = QThread()
        self.populaterThread.started.connect(self.populater.started)

        self.populater.moveToThread(self.populaterThread)
        self.populaterThread.start()

        self.add_folder.emit("Txt2Img", "outputs/txt2img")

        parent.aboutToQuit.connect(self.stop)

    @pyqtSlot()
    def stop(self):
        self.populaterThread.quit()
        self.populaterThread.wait()