import io
import os

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QMutex, QRunnable, QThreadPool, QUrl, QByteArray, QThread, QSize
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtQuick import QQuickImageProvider, QQuickAsyncImageProvider, QQuickImageResponse, QQuickTextureFactory
from PyQt5.QtGui import QImage

import PIL.Image

import filesystem
import sql

def get_thumbnail(file, size, quality):
    blob = io.BytesIO()
    image = PIL.Image.open(file)
    image.thumbnail(size, PIL.Image.ANTIALIAS)
    image.save(blob, "JPEG", quality=quality)
    return blob.getvalue()

class ThumbnailStorage(QObject):
    instance = None
    def __init__(self, size, quality, parent=None):
        super().__init__(parent)
        self.cache = {}
        self.guard = QMutex()
        ThumbnailStorage.instance = self

        self.async_provider = AsyncThumbnailProvider(size, quality)
        self.sync_provider = SyncThumbnailProvider(size, quality)

    def get(self, file):
        self.guard.lock()
        image = self.cache.get(file, None)
        self.guard.unlock()
        return image
    def put(self, file, image):
        self.guard.lock()
        self.cache[file] = image
        self.guard.unlock()
    def has(self, file):
        self.guard.lock()
        out = file in self.cache
        self.guard.unlock()
        return out
    def remove(self, file):
        self.guard.lock()
        if file in self.cache:
            del self.cache[file]
        self.guard.unlock()

class ThumbnailResponseRunnableSignals(QObject):
    done = pyqtSignal('QImage')

class ThumbnailResponseRunnable(QRunnable):
    def __init__(self, file, size, quality):
        super().__init__()
        self.size = size
        self.quality = quality
        self.file = file
        self.signals = ThumbnailResponseRunnableSignals()
        self.image = None

    def run(self):
        try:
            blob = get_thumbnail(self.file, self.size, self.quality)
            ThumbnailStorage.instance.put(self.file, blob)
            self.image = QImage.fromData(QByteArray(blob), "JPG")
        except Exception:
            self.image = QImage()

        self.signals.done.emit(self.image)

class ThumbnailResponse(QQuickImageResponse):
    def __init__(self, file, pool, size, quality):
        super().__init__()
        blob = ThumbnailStorage.instance.get(file)
        if not blob:
            runnable = ThumbnailResponseRunnable(file, size, quality)
            runnable.signals.done.connect(self.onDone)
            pool.start(runnable)
        else:
            self.image = QImage.fromData(QByteArray(blob), "JPG")
            self.finished.emit()       
    
    @pyqtSlot('QImage')
    def onDone(self, image):
        self.image = image
        self.finished.emit()
    
    def textureFactory(self):
        return QQuickTextureFactory.textureFactoryForImage(self.image)

class AsyncThumbnailProvider(QQuickAsyncImageProvider):
    def __init__(self, size, quality):
        super(AsyncThumbnailProvider, self).__init__()
        self.size = size
        self.quality = quality
        self.pool = QThreadPool()

    def requestImageResponse(self, path, size):
        file = QUrl(path).path()
        return ThumbnailResponse(file, self.pool, self.size, self.quality)

class SyncThumbnailProvider(QQuickImageProvider):
    def __init__(self, size, quality):
        super(SyncThumbnailProvider, self).__init__(QQuickImageProvider.Image)
        self.size = size
        self.quality = quality

    def requestImage(self, path, size):
        file = QUrl(path).path()
        try:
            blob = ThumbnailStorage.instance.get(file)
            if not blob:
                blob = get_thumbnail(file, self.size, self.quality)
                ThumbnailStorage.instance.put(file, blob)

            image = QImage.fromData(QByteArray(blob), "JPG")
            return image, image.size()
        except Exception:
            return QImage(), QSize(0,0)