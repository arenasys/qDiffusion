import PIL.Image
import shutil
import os
import send2trash
import glob

from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QObject, QThread, QUrl, QMimeData, Qt
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication
import sql
import filesystem
import parameters
import time

class Populater(QObject):
    forceReload = pyqtSignal(str)
    stop = pyqtSignal(str)
    def __init__(self, gui, name):
        super().__init__()
        self.paths = []
        self.gui = gui
        self.name = name

        self.primary = ""
        self.remaining = []

        self.output = self.gui.outputDirectory()

        self.order = ["txt2img", "img2img", "favourites"]
        self.labels = {"txt2img": "Txt2Img", "img2img": "Img2Img"}

        for s in self.order:
            os.makedirs(os.path.join(self.output, s), exist_ok=True)

        self.conn = None
        self.watcher = gui.watcher
        self.disabled = gui.debugMode() == 2
        self.folders = set()
        self.working = set()
        self.fresh = set()
        self.initial = True

    @pyqtSlot()
    def started(self):
        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE folders(folder TEXT UNIQUE, name TEXT UNIQUE, idx INTEGER UNIQUE);")
        self.conn.doQuery("CREATE TABLE images(file TEXT UNIQUE, folder TEXT, parameters TEXT, idx INTEGER, width INTEGER, height INTEGER, CONSTRAINT unq UNIQUE (folder, idx));")
        self.conn.enableNotifications("folders")
        self.conn.disableNotifications("images")

        self.prepareFolders()

        if self.disabled:
            return

        self.watcher.finished.connect(self.onFinished)
        self.watcher.folder_changed.connect(self.onResult)
        self.watcher.parent_changed.connect(self.onParentChanged)

    def prepareFolders(self):
        subfolders = [s.rsplit(os.path.sep,1)[-1] for s in list(filter(os.path.isdir, glob.glob(self.output + "/*")))]
        subfolders = [o for o in self.order if o in subfolders] + [s for s in subfolders if not s in self.order]

        self.primary = ""
        self.remaining = []

        for idx, name in enumerate(subfolders):
            label = self.labels.get(name, name.capitalize())
            folder = os.path.join(self.output, name)
            
            if idx == 0:
                self.primary = folder
                if not self.disabled:
                    self.watcher.watchFolder(self.primary)
            else:
                self.remaining += [folder]

            q = QSqlQuery(self.conn.db)
            q.prepare("INSERT OR REPLACE INTO folders(folder, name, idx) VALUES (:folder, :name, :idx);")
            q.bindValue(":folder", folder)
            q.bindValue(":name", label)
            q.bindValue(":idx", idx)
            self.conn.doQuery(q)
            self.folders.add(folder)
            self.fresh.add(folder)

        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM folders WHERE idx >= :total;")
        q.bindValue(":total", len(subfolders))
        self.conn.doQuery(q)

    def resumeFolders(self):
        for subfolder in self.remaining:
            if not self.disabled:
                self.watcher.watchFolder(subfolder)
        self.primary = ""
        self.remaining = []

    @pyqtSlot(str)
    def onParentChanged(self, folder):
        if folder == self.output:
            self.prepareFolders()

    @pyqtSlot(str, int)
    def onFinished(self, folder, total):
        if not folder in self.folders:
            return

        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM images WHERE folder == :folder AND idx >= :total;")
        q.bindValue(":folder", folder)
        q.bindValue(":total", total)
        self.conn.doQuery(q)

        self.working.discard(folder)
        self.fresh.discard(folder)
        if len(self.working) == 0 and len(self.fresh) == 0:
            self.gui.setTabWorking(self.name, False)

        if folder == self.primary:
            self.conn.enableNotifications("images")
            self.initial = False
            self.resumeFolders()

    @pyqtSlot(str, list, list)
    def onResult(self, folder, files, idxs):
        if not folder in self.folders:
            return
        
        if len(self.working) == 0:
            self.gui.setTabWorking(self.name, True)
        self.working.add(folder)

        data = zip(files, idxs)
        
        files, folders, idxs, widths, heights, parameters = [], [], [], [], [], []
        for f, i in data:
            if not f.split(".")[-1] in {"png"}:
                continue
            w, h, p = 0, 0, ""
            try:
                with PIL.Image.open(f) as img:
                    if "parameters" in img.info:
                        p = img.info["parameters"]
                    w, h = img.size
            except Exception:
                continue
            if w == 0 or h == 0:
                continue
            files += [f]
            folders += [folder]
            idxs += [i]
            widths += [w]
            heights += [h]
            parameters += [p.replace("'", "''")]

        q = QSqlQuery(self.conn.db)
        q.prepare(f"INSERT OR REPLACE INTO images(file, folder, parameters, idx, width, height) VALUES (:file, :folder, :param, :idx, :width, :height);")
        q.bindValue(":file", files)
        q.bindValue(":folder", folders)
        q.bindValue(":param", parameters)
        q.bindValue(":idx", idxs)
        q.bindValue(":width", widths)
        q.bindValue(":height", heights)
        q.execBatch()

        if self.initial:
            self.forceReload.emit(folder)

class Deleter(QThread):
    def __init__(self, gui, files):
        super().__init__()
        self.files = files
        self.gui = gui
    def run(self):
        try:
            send2trash.send2trash(self.files)
        except OSError:
            for f in self.files:
                os.remove(f)
        self.gui.thumbnails.removeAll(self.files)

class Gallery(QObject):
    update = pyqtSignal()

    forceReload = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 3
        self.name = "History"
        self.folder = ""

        self._cellSize = 200

        qmlRegisterSingletonType(Gallery, "gui", 1, 0, "GALLERY", lambda qml, js: self)

        self.populater = Populater(self.gui, self.name)
        self.populater.forceReload.connect(self.populaterForcedReload)

        self.populaterThread = QThread()
        self.populaterThread.started.connect(self.populater.started)

        self.populater.moveToThread(self.populaterThread)
        self.populaterThread.start()

        parent.aboutToQuit.connect(self.stop)

        self.deleters = []
    
    @pyqtSlot(list)
    def doOpenFiles(self, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        self.gui.openFiles(files)

    @pyqtSlot(list)
    def doVisitFiles(self, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        self.gui.visitFiles(files)

    @pyqtSlot(str, list)
    def doCopy(self, folder, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        idx = parameters.getIndex(folder)
        for src in files:
            dst = os.path.join(folder, f"{idx:07d}.png")
            shutil.copy(src, dst)
            idx += 1

    @pyqtSlot(str, list)
    def doMove(self, folder, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        idx = parameters.getIndex(folder)
        for src in files:
            dst = os.path.join(folder, f"{idx:07d}.png")
            shutil.move(src, dst)
            idx += 1

    @pyqtSlot(list)
    def doDelete(self, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        deleter = Deleter(self.gui, files)
        deleter.start()
        self.deleters += [deleter]

    @pyqtSlot(list)
    def doClipboard(self, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        self.gui.copyFiles(files)

    @pyqtSlot(list)
    def doDrag(self, files):
        files = [os.path.abspath(f) for f in files if os.path.exists(f)]
        if not files:
            return
        
        self.gui.dragFiles(files)

    @pyqtSlot()
    def stop(self):
        self.populaterThread.quit()
        self.populaterThread.wait()

    @pyqtProperty(int, notify=update)
    def cellSize(self):
        return self._cellSize

    @pyqtSlot(int)
    def adjustCellSize(self, adj):
        cellSize = self._cellSize + adj
        if cellSize >= 100 and cellSize <= 200:
            self._cellSize = cellSize
            self.update.emit()
        
    @pyqtSlot(str)
    def populaterForcedReload(self, folder):
        if folder == self.folder:
            self.forceReload.emit()

    @pyqtProperty(str, notify=update)
    def currentFolder(self):
        return self.folder
    
    @currentFolder.setter
    def currentFolder(self, folder):
        self.folder = folder