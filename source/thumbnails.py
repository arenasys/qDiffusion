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
    image = PIL.Image.open(file).convert('RGB')
    image.thumbnail(size, PIL.Image.ANTIALIAS)
    image.save(blob, "JPEG", quality=quality)
    return blob.getvalue()

class ThumbnailStorage(QObject):
    instance = None
    def __init__(self, size, big_size, quality, parent=None):
        super().__init__(parent)
        self.cache = {size: {}, big_size: {}}
        self.guard = QMutex()
        ThumbnailStorage.instance = self

        self.async_provider = AsyncThumbnailProvider(size, quality)
        self.sync_provider = SyncThumbnailProvider(size, quality)
        self.big_provider = AsyncThumbnailProvider(big_size, quality)

    def get(self, file, size):
        self.guard.lock()
        image = self.cache[size].get(file, None)
        self.guard.unlock()
        return image
    def put(self, file, image, size):
        self.guard.lock()
        self.cache[size][file] = image
        self.guard.unlock()
    def has(self, file, size):
        self.guard.lock()
        out = file in self.cache[size]
        self.guard.unlock()
        return out
    def remove(self, file):
        self.guard.lock()
        for size in self.cache:
            if file in self.cache[size]:
                del self.cache[size][file]
        self.guard.unlock()
    def removeAll(self, files):
        self.guard.lock()
        for size in self.cache:
            for file in files:
                if file in self.cache[size]:
                    del self.cache[size][file]
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
            ThumbnailStorage.instance.put(self.file, blob, self.size)
            self.image = QImage.fromData(QByteArray(blob), "JPG")
        except Exception as e:
            #print(e)
            self.image = QImage()

        self.signals.done.emit(self.image)

class ThumbnailResponse(QQuickImageResponse):
    def __init__(self, file, pool, size, quality):
        super().__init__()
        file = QUrl.fromLocalFile(file).toLocalFile()
        blob = ThumbnailStorage.instance.get(file, size)
        if not blob:
            runnable = ThumbnailResponseRunnable(file, size, quality)
            runnable.signals.done.connect(self.onDone)
            pool.start(runnable)
        else:
            self.image = QImage.fromData(QByteArray(blob), "JPG")
            self.finished.emit()       
    
    @pyqtSlot('QImage')
    def onDone(self, image):
        self.image = QImage(image)
        self.finished.emit()
    
    def textureFactory(self):
        self.texture = QQuickTextureFactory.textureFactoryForImage(self.image)
        return self.texture

class AsyncThumbnailProvider(QQuickAsyncImageProvider):
    def __init__(self, size, quality):
        super(AsyncThumbnailProvider, self).__init__()
        self.size = size
        self.quality = quality
        self.pool = QThreadPool.globalInstance()

    def requestImageResponse(self, path, size):
        file = QUrl.fromPercentEncoding(path.encode('utf-8'))
        return ThumbnailResponse(file, self.pool, self.size, self.quality)

class SyncThumbnailProvider(QQuickImageProvider):
    def __init__(self, size, quality):
        super(SyncThumbnailProvider, self).__init__(QQuickImageProvider.Image)
        self.size = size
        self.quality = quality

    def requestImage(self, path, size):
        file = QUrl.fromPercentEncoding(path.encode('utf-8'))
        try:
            blob = ThumbnailStorage.instance.get(file, self.size)
            if not blob:
                blob = get_thumbnail(file, self.size, self.quality)
                ThumbnailStorage.instance.put(file, blob, self.size)

            image = QImage.fromData(QByteArray(blob), "JPG")
            return image, image.size()
        except Exception as e:
            #print(e)
            return QImage(), QSize(0,0)