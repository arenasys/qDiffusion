from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, Qt, QPointF, QRectF
from PyQt5.QtQuick import QQuickPaintedItem
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QPainterPath, QPen, QPolygonF, QImage, QConicalGradient, QRadialGradient
from PyQt5.QtQml import qmlRegisterType
import time

from canvas.shared import CanvasSelectionMode
from canvas.canvas import CanvasTool, CanvasSelection

class ImageDisplay(QQuickPaintedItem):
    imageUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._centered = False

    @pyqtProperty(QImage, notify=imageUpdated)
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._image = image

        self.setImplicitHeight(image.height())
        self.setImplicitWidth(image.width())
        self.imageUpdated.emit()
        self.update()

    @pyqtProperty(bool, notify=imageUpdated)
    def centered(self):
        return self._centered
    
    @centered.setter
    def centered(self, centered):
        self._centered = centered
        self.imageUpdated.emit()
        self.update()

    def paint(self, painter):
        if self._image and not self._image.isNull():
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio)
            x, y = 0, 0
            if self.centered:
                x = int((self.width() - img.width())/2)
                y = int((self.height() - img.height())//2)
            painter.drawImage(x,y,img)

class ColorRadial(QQuickPaintedItem):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lightness = 1.0
        self._angle = 0.0
        self._radius = 0.0
        self._color = QColor(0xFFFFFF)
        self.setAntialiasing(True)

    @pyqtProperty(float, notify=updated)
    def lightness(self):
        return self._lightness
    
    @lightness.setter
    def lightness(self, lightness):
        self._lightness = lightness
        self.update()

    @pyqtProperty(float, notify=updated)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle = angle
        self.update()

    @pyqtProperty(float, notify=updated)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, radius):
        self._radius = radius
        self.update()

    @pyqtProperty(float, notify=updated)
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha
        self.update()

    @pyqtProperty(QColor, notify=updated)
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.update()

    def paint(self, painter):
        painter.setPen(Qt.NoPen)

        radius = min(self.width(), self.height())//2
        center = QPointF(self.width()//2, self.height()//2)

        self._color = QColor.fromHsvF(self._angle, self._radius, self._lightness, self._alpha)
        self.updated.emit()

        hue = QConicalGradient(center, 270)
        samples = int(radius)
        for i in range(0, samples+1):
            hue.setColorAt(1-(i/samples), QColor.fromHsvF(i/samples, 1, 1))

        painter.setBrush(hue)
        painter.drawEllipse(center, radius, radius)
        
        value = QRadialGradient(center, radius)
        value.setColorAt(0, QColor.fromHsvF(0, 0, 1))
        value.setColorAt(1, QColor.fromHsvF(0, 0, 1, 0.0))

        painter.setBrush(value)
        painter.drawEllipse(center, radius, radius)

        painter.setBrush(QColor.fromRgbF(0,0,0,1-self._lightness))
        painter.drawEllipse(center, radius, radius)        

class MarchingAnts(QQuickPaintedItem):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selection = None
        self._factor = 1.0
        self._offset = QPointF()
        self._dash = 0
        self._last = time.time_ns()
        self._shader = False
        self._needsUpdate = False
        self._pathOffset = QPointF()
    
    @pyqtProperty(CanvasSelection, notify=updated)
    def selection(self):
        return self._selection
    
    @selection.setter
    def selection(self, selection):
        self._selection = selection
        self._needsUpdate = True
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def factor(self):
        return self._factor
    
    @factor.setter
    def factor(self, factor):
        self._factor = factor
        self._needsUpdate = True
        self.updated.emit()

    @pyqtProperty(QPointF, notify=updated)
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = offset
        self._needsUpdate = True
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def dash(self):
        return self._dash

    @pyqtProperty(bool, notify=updated)
    def shader(self):
        return self._shader
    
    @pyqtProperty(bool, notify=updated)
    def needsUpdate(self):
        return self._needsUpdate
    
    @pyqtSlot()
    def requestUpdate(self):
        self._needsUpdate = True
        self.updated.emit()

    def process(self, shape):
        if type(shape.bound) == QRectF:
            return shape.transform(self._offset, self._factor).bound
        else:
            return QPolygonF(shape.transform(self._offset, self._factor).bound)
    
    def paintPath(self, painter, path):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor.fromRgbF(1.0, 0.0, 0.0))
        painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)
    
        pen = QPen()
        pen.setWidth(3)
        pen.setColor(QColor.fromRgbF(1.0, 1.0, 1.0))
        pen.setDashPattern([2,4])
        pen.setDashOffset(self._dash)
        painter.setPen(pen)
        painter.drawPath(path)

        pen.setWidth(3)
        pen.setColor(QColor.fromRgbF(0.0, 0.0, 0.0))
        pen.setDashOffset(self._dash+3)
        painter.setPen(pen)
        painter.drawPath(path)

    def addPath(self, painter, path):
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        self.paintPath(painter, path)

    def subtractPath(self, painter, path):
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        self.paintPath(painter, path)
        painter.setBrush(QColor.fromRgbF(1.0, 0.0, 0.0))
        painter.setPen(Qt.NoPen)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawPath(path)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def paint(self, painter):
        if not self._selection.visible:
            return

        diff = ((time.time_ns() - self._last)//1000000)
        self._dash = (self._dash + (diff / 500)) % 6.0
        self._last = time.time_ns()
        self._needsUpdate = False
        self.updated.emit()
        
        shapes = self._selection.shapes

        for shape in shapes:
            path = QPainterPath()
            bound = self.process(shape)
            if shape.tool == CanvasTool.RECTANGLE_SELECT:
                path.addRect(bound)
            elif shape.tool == CanvasTool.ELLIPSE_SELECT:
                path.addEllipse(bound.adjusted(0,0,0,-0.0001))
            elif shape.tool == CanvasTool.PATH_SELECT and len(bound) >= 3:
                path.addPolygon(bound)

            if shape.mode == CanvasSelectionMode.SUBTRACT:
                self.subtractPath(painter, path)
            else:
                self.addPath(painter, path)

def registerMiscTypes():
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(ColorRadial, "gui", 1, 0, "ColorRadial")
    qmlRegisterType(MarchingAnts, "gui", 1, 0, "MarchingAnts")