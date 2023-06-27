from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, Qt, QObject, QPointF, QRectF, QMimeData, QSizeF
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QPainterPath, QPen, QPolygonF, QImage, QConicalGradient, QRadialGradient
from PyQt5.QtQml import qmlRegisterType
import time


class ColorRadial(QQuickPaintedItem):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lightness = 1.0
        self._angle = 0.0
        self._alpha = 1.0
        self._radius = 0.0
        self._color = QColor(0xFFFFFF)
        self.setAntialiasing(True)
        self._painted = False

    @pyqtProperty(float, notify=updated)
    def lightness(self):
        return self._lightness
    
    @lightness.setter
    def lightness(self, lightness):
        if self._lightness != lightness:
            self._lightness = lightness
            self.update()

    @pyqtProperty(float, notify=updated)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        if self._angle != angle:
            self._angle = angle
            self.update()

    @pyqtProperty(float, notify=updated)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, radius):
        if self._radius != radius:
            self._radius = radius
            self.update()

    @pyqtProperty(float, notify=updated)
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        if self._alpha != alpha:
            self._alpha = alpha
            self.update()

    @pyqtProperty(float, notify=updated)
    def opacity(self):
        # need a duplicate binding spot for QML side
        return self._alpha

    @opacity.setter
    def opacity(self, alpha):
        if self._alpha != alpha:
            self._alpha = alpha
            self.update()

    @pyqtProperty(QColor, notify=updated)
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if self._color.name(QColor.HexArgb) != color.name(QColor.HexArgb):
            self._color = color
            self._angle = color.hsvHueF()
            self._radius = color.hsvSaturationF()
            self._lightness = color.valueF()
            self._alpha = color.alphaF()
            
            self.update()
    @pyqtProperty(str, notify=updated)
    def hex(self):
        if self._color.alphaF() == 1.0:
            return self._color.name(QColor.HexRgb)
        else:
            return self._color.name(QColor.HexArgb)
    
    @hex.setter
    def hex(self, hex):
        if len(hex) == 7:
            curr = self._color.name(QColor.HexRgb)
        else:
            curr = self._color.name(QColor.HexArgb)

        if hex != curr:
            self.color = QColor(hex)
            self.update()

    def paint(self, painter):
        radius = min(self.width(), self.height())//2
        center = QPointF(self.width()//2, self.height()//2)
        self._color = QColor.fromHsvF(self._angle, self._radius, self._lightness, self._alpha)
        self.updated.emit()

        print("", end="") # wtf

        painter.setPen(Qt.NoPen)

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

def registerMiscTypes():
    qmlRegisterType(ColorRadial, "gui", 1, 0, "ColorRadial")