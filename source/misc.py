import re
import os
import ctypes
import math 

try:
    ctypes.windll.ole32.CoInitialize.restype = ctypes.HRESULT
    ctypes.windll.ole32.CoInitialize.argtypes = [ctypes.c_void_p]
    ctypes.windll.ole32.CoUninitialize.restype = None
    ctypes.windll.ole32.CoUninitialize.argtypes = None
    ctypes.windll.shell32.ILCreateFromPathW.restype = ctypes.c_void_p
    ctypes.windll.shell32.ILCreateFromPathW.argtypes = [ctypes.c_char_p]
    ctypes.windll.shell32.SHOpenFolderAndSelectItems.restype = ctypes.HRESULT
    ctypes.windll.shell32.SHOpenFolderAndSelectItems.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_ulong]
    ctypes.windll.shell32.ILFree.restype = None
    ctypes.windll.shell32.ILFree.argtypes = [ctypes.c_void_p]
except Exception:
    pass

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QByteArray, QBuffer, QIODevice
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QColor, QPen, QImage, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtQml import qmlRegisterType

class FocusReleaser(QQuickItem):
    releaseFocus = pyqtSignal()
    dropped = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setFiltersChildMouseEvents(True)
    
    def onPress(self, source):
        if not source.hasActiveFocus():
            self.releaseFocus.emit()

    def childMouseEventFilter(self, child, event):
        if event.type() == QEvent.MouseButtonPress:
            self.onPress(child)
        return False

    def mousePressEvent(self, event):
        self.onPress(self)
        event.setAccepted(False)

class ImageDisplay(QQuickPaintedItem):
    imageUpdated = pyqtSignal()
    sizeUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._centered = False
        self._trueWidth = 0
        self._trueHeight = 0
        self._trueX = 0
        self._trueY = 0

    @pyqtProperty(QImage, notify=imageUpdated)
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._last = None
        self._image = image

        self.setImplicitHeight(image.height())
        self.setImplicitWidth(image.width())
        self.imageUpdated.emit()

        if self._image and not self._image.isNull():
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio)
            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self._trueX, self._trueY = self.arrange(img)
                self.sizeUpdated.emit()
        else:
            self._trueWidth = 0
            self._trueHeight = 0
            self.sizeUpdated.emit()

        self.update()

    @pyqtSlot(result=QImage)
    def clear(self):
        return QImage()

    @pyqtProperty(bool, notify=imageUpdated)
    def centered(self):
        return self._centered
    
    @centered.setter
    def centered(self, centered):
        self._centered = centered
        self.imageUpdated.emit()
        self.update()

    @pyqtProperty(int, notify=sizeUpdated)
    def trueWidth(self):
        return self._trueWidth
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueHeight(self):
        return self._trueHeight
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueX(self):
        return self._trueX
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueY(self):
        return self._trueY

    @pyqtProperty(int, notify=imageUpdated)
    def sourceWidth(self):
        if self._image:
            return self._image.width()
        return 0
    
    @pyqtProperty(int, notify=imageUpdated)
    def sourceHeight(self):
        if self._image:
            return self._image.height()
        return 0
    
    def arrange(self, img):
        x, y = 0, 0
        if self.centered:
            x = int((self.width() - img.width())/2)
            y = int((self.height() - img.height())//2)
        return x, y

    def paint(self, painter):
        if self._image and not self._image.isNull():
            transform = Qt.SmoothTransformation
            if not self.smooth():
                transform = Qt.FastTransformation

            # FIX THIS CRAP
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio, transform)
            x, y = self.arrange(img)

            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self._trueX = x
                self._trueY = y
                self.sizeUpdated.emit()
            painter.drawImage(x,y,img)

class MimeData(QObject):
    def __init__(self, mimeData, parent=None):
        super().__init__(parent)
        self._mimeData = mimeData

    @pyqtProperty(QMimeData)
    def mimeData(self):
        return self._mimeData

class DropArea(QQuickItem):
    dropped = pyqtSignal(MimeData, arguments=["mimeData"])
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QQuickItem.ItemAcceptsDrops, True)
        self._containsDrag = False
        self._filters = []
    
    @pyqtProperty(bool, notify=updated)
    def containsDrag(self):
        return self._containsDrag
    
    @pyqtProperty(list, notify=updated)
    def filters(self):
        return self._filters

    @filters.setter
    def filters(self, filters):
        self._filters = filters
        self.updated.emit()

    def dragEnterEvent(self, enter):
        formats = enter.mimeData().formats()
        if not self._filters or any([f in formats for f in self._filters]):
            enter.accept()
            self._containsDrag = True
            self.updated.emit()

    def dragLeaveEvent(self, leave):
        leave.accept()
        self._containsDrag = False
        self.updated.emit()

    def dragMoveEvent(self, move):
        formats = move.mimeData().formats()
        if not self._filters or any([f in formats for f in self._filters]):
            move.accept()

    def dropEvent(self, drop):
        formats = drop.mimeData().formats()
        if not self._filters or any([f in formats for f in self._filters]):
            drop.accept()
            self._containsDrag = False
            self.updated.emit()
            self.dropped.emit(MimeData(drop.mimeData()))

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
    def highlightBlock(self, text):
        text = text + " "
        emb = QColor("#ffd893")
        lora_bg = QColor("#f9c7ff")
        lora = QColor("#d693ff")
        hn_bg = QColor("#c7fff6")
        hn = QColor("#93d6ff")
        err_bg = QColor("#ffc4c4")
        err = QColor("#ff9393")
        wild_bg = QColor("#c7ffd2")
        wild = QColor("#93ffa9")
        field = QColor("#9e9e9e")
        keyword = QColor("#ffb393")

        embeddings = set()
        if "TI" in self.gui._options:
            embeddings = set([self.gui.modelName(n) for n in self.gui._options["TI"]])

        loras = set()
        if "LoRA" in self.gui._options:
            loras = set([self.gui.modelName(n) for n in self.gui._options["LoRA"]])

        hns = set()
        if "HN" in self.gui._options:
            hns = set([self.gui.modelName(n) for n in self.gui._options["HN"]])

        wilds = set(self.gui.wildcards._wildcards.keys())

        for em in embeddings:
            for s, e  in [m.span() for m in re.finditer(em, text)]:
                self.setFormat(s, e-s, emb)
        
        for s, e, ms, me in [(*m.span(0), *m.span(1)) for m in re.finditer("<@?lora:([^:>]+)([^>]+)?>", text.lower())]:
            m = text[ms:me]
            if m in loras:
                self.setFormat(s, e-s, lora_bg)
                self.setFormat(ms, me-ms, lora)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,lora)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,err)
        
        for s, e, ms, me in [(*m.span(0), *m.span(1))  for m in re.finditer("<@?hypernet:([^:>]+)([^>]+)?>", text.lower())]:
            m = text[ms:me]
            if m in hns:
                self.setFormat(s, e-s, hn_bg)
                self.setFormat(ms, me-ms, hn)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,hn)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,err)

        for s, e, ms, me in [(*m.span(0), *m.span(1)) for m in re.finditer("@?__([^\s]+?)__(?!___)", text)]:
            m = text[ms:me]
            if m in wilds:
                self.setFormat(s, e-s, wild_bg)
                self.setFormat(ms, me-ms, wild)
                if text[s] == "@":
                    self.setFormat(s,1,wild)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s] == "@":
                    self.setFormat(s,1,err)

        for s, e in [m.span(0) for m in re.finditer("((?<=\s|,)|^)(AND|BREAK|START|END)(?=\s|,|$)", text)]:
            self.setFormat(s, e-s, keyword)
        
        if text.startswith("Negative prompt: "):
            self.setFormat(0, 16, field)
        
        if text.startswith("Steps: "):
            for s, e in [m.span(1) for m in re.finditer("(?:\s)?([^,:]+):[^,]+(,)?", text.lower())]:
                self.setFormat(s, e-s, field)

def encodeImage(img):
    ba = QByteArray()
    bf = QBuffer(ba)
    bf.open(QIODevice.WriteOnly)
    img.save(bf, "PNG")
    return ba.data()

def cropImage(img, size, offset = 0.5):
    in_z = img.size()
        
    ar = size.width()/size.height()

    rh = in_z.height()/size.height()
    rw = in_z.width()/size.width()

    w, h = in_z.width(), in_z.height()

    if size.width() * rh > in_z.width():
        h = math.ceil(w / ar)
    elif size.height() * rw > in_z.height():
        w = math.ceil(h * ar)

    dx = int((in_z.width()-w)*offset)
    dy = int((in_z.height()-h)*offset)

    return img.copy(dx, dy, w, h)

def registerTypes():
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(FocusReleaser, "gui", 1, 0, "FocusReleaser")
    qmlRegisterType(DropArea, "gui", 1, 0, "AdvancedDropArea")
    qmlRegisterType(MimeData, "gui", 1, 0, "MimeData")

def showFilesInExplorer(folder, files):
    ctypes.windll.ole32.CoInitialize(None)

    files = [os.path.normpath(f) for f in files]
    folder = os.path.normpath(folder)
    count = len(files)

    folder_pidl = ctypes.windll.shell32.ILCreateFromPathW(folder.encode('utf-16le') + b'\0')
    files_pidl = [
        ctypes.windll.shell32.ILCreateFromPathW(f.encode('utf-16le') + b'\0') for f in files
    ]

    files_pidl_arr = (ctypes.c_void_p * count)(*files_pidl)

    ctypes.windll.shell32.SHOpenFolderAndSelectItems(folder_pidl, count, files_pidl_arr, 0)

    for pidl in files_pidl[::-1]:
        ctypes.windll.shell32.ILFree(pidl)
    ctypes.windll.shell32.ILFree(folder_pidl)

    ctypes.windll.ole32.CoUninitialize()

NATSORT_KEY = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

def sortFiles(files):
    return sorted(files, key=lambda f: NATSORT_KEY(f.rsplit(os.path.sep,1)[-1]))