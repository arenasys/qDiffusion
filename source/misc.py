from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage
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
                self.sizeUpdated.emit()
        else:
            self._trueWidth = 0
            self._trueHeight = 0
            self.sizeUpdated.emit()

        self.update()

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

    def paint(self, painter):
        if self._image and not self._image.isNull():
            transform = Qt.SmoothTransformation
            if not self.smooth():
                transform = Qt.FastTransformation

            # FIX THIS CRAP
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio, transform)
            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self.sizeUpdated.emit()
            x, y = 0, 0
            if self.centered:
                x = int((self.width() - img.width())/2)
                y = int((self.height() - img.height())//2)
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
    
    @pyqtProperty(bool, notify=updated)
    def containsDrag(self):
        return self._containsDrag
    
    def dragEnterEvent(self, enter): 
        enter.accept()
        self._containsDrag = True
        self.updated.emit()

    def dragLeaveEvent(self, leave): 
        leave.accept()
        self._containsDrag = False
        self.updated.emit()

    def dragMoveEvent(self, move):
        move.accept()

    def dropEvent(self, drop):
        drop.accept()
        self._containsDrag = False
        self.updated.emit()
        self.dropped.emit(MimeData(drop.mimeData()))

def registerTypes():
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(FocusReleaser, "gui", 1, 0, "FocusReleaser")
    qmlRegisterType(DropArea, "gui", 1, 0, "AdvancedDropArea")
    qmlRegisterType(MimeData, "gui", 1, 0, "MimeData")