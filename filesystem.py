import glob
import os

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThreadPool, QRunnable, QFileSystemWatcher

class WatcherRunnableSignals(QObject):
    result = pyqtSignal(str, str, int)
    finished = pyqtSignal(str, int)
    def __init__(self, folder):
        super().__init__()
        self.stopping = False
        self.folder = folder

    @pyqtSlot(str)
    def die(self, folder):
        if folder == self.folder:
            self.stopping = True

class WatcherRunnable(QRunnable):
    found_image = pyqtSignal(int, str, str, str)
    def __init__(self, folder):
        super(WatcherRunnable, self).__init__()
        self.signals = WatcherRunnableSignals(folder)
        self.folder = folder
    
    @pyqtSlot()
    def run(self):
        try:
            files = glob.glob(os.path.join(self.folder, "*.*"))
            files = sorted(files, key = os.path.getmtime)
            for i, file in enumerate(files):
                if self.signals.stopping:
                    return
                self.signals.result.emit(self.folder, file, i)
            if not self.signals.stopping:
                self.signals.finished.emit(self.folder, len(files))
        except Exception:
            return

class Watcher(QObject):
    started = pyqtSignal(str)
    result = pyqtSignal(str, str, int)
    finished = pyqtSignal(str, int)
    kill = pyqtSignal(str)

    instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(self.folder_changed)

        self.folders = set()
        self.parents = {}

        self.pool = QThreadPool()
        self.running = {}

        Watcher.instance = self

        self.stopping = False

    @pyqtSlot()
    def stop(self):
        self.stopping = True
        self.pool.waitForDone()
        
    @pyqtSlot(str)
    def watch_folder(self, folder):
        self.folders.add(folder)
        parentFolder = os.path.dirname(folder)
        self.parents[folder] = parentFolder

        self.watcher.addPath(folder)
        self.watcher.addPath(parentFolder)

        self.watcher_start(folder)

    @pyqtSlot(str)
    def unwatch_folder(self, folder):
        self.kill.emit(folder)

        self.folders.remove(folder)
        parent = self.parents[folder]
        del self.parents[folder]

        self.watcher.removePath(folder)
        if not parent in self.parents.values():
            self.watcher.removePath(parent)

    def watcher_start(self, folder):
        if self.stopping:
            return

        if folder in self.running:
            self.running[folder].signals.result.disconnect()
            self.running[folder].signals.finished.disconnect()
            self.kill.emit(folder)
        
        watcher = WatcherRunnable(folder)
        watcher.signals.result.connect(self.on_watcher_result)
        watcher.signals.finished.connect(self.on_watcher_finished)
        self.kill.connect(watcher.signals.die)

        self.running[folder] = watcher

        watcher.setAutoDelete(True)
        self.pool.start(watcher)
        self.started.emit(folder)
    
    @pyqtSlot(str)
    def folder_changed(self, folder):
        if folder in self.folders:
            self.watcher_start(folder)
            return
        else:
            for child, parent in self.parents.items():
                if parent == folder:
                    self.watcher.addPath(child)
                    self.watcher_start(child)

    @pyqtSlot(str, int)
    def on_watcher_finished(self, folder, total):
        del self.running[folder]
        self.finished.emit(folder, total)

    @pyqtSlot(str, str, int)
    def on_watcher_result(self, folder, file, idx):
        self.result.emit(folder, file, idx)