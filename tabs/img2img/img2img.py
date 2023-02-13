from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, Qt, QRectF, QPointF, QSize
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtQuick import QQuickFramebufferObject
from PyQt5.QtGui import QFont, QRadialGradient, QPen, QBrush, QColor, QPainter, QPaintDevice, QOpenGLPaintDevice
import math
import copy

class img2img(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Img2Img"
        qmlRegisterSingletonType(img2img, "gui", 1, 0, "IMG2IMG", lambda qml, js: self)
        qmlRegisterType(ImageCanvas, "gui", 1, 0, "ImageCanvas")

class ImageCanvasStates():
    def __init__(self):
        self.brushSize = 20
        self.brushSpacing = 0.1
        self.brushColor = QColor.fromRgbF(1, 0, 0, 1)
        self.brushHardness = 0.5
        self.strokePositions = []

    def synchronize(self):
        out = copy.copy(self)
        self.clearStroke()
        return out

    def addStroke(self, position):
        self.strokePositions.append(position)

    def clearStroke(self):
        self.strokePositions = []

    def getBrushAbsoluteSpacing(self):
        return self.brushSize * self.brushSpacing

    def getBrushColor(self, radius):
        alpha = 1.0
        if self.brushHardness != 1:
            alpha = ((math.cos(radius*math.pi)+1)/2)**(1/(2*self.brushHardness))

        color = QColor(self.brushColor)
        color.setAlphaF(alpha)
        return color

class ImageCanvasRenderer(QQuickFramebufferObject.Renderer):
    def __init__(self, parent=None, size=None):
        super().__init__()
        self.size = size
        self.states = None
    
    def createFramebufferObject(self, size):
        return super().createFramebufferObject(self.size)
    
    def synchronize(self, item):
        self.states = item.states.synchronize()

    def render(self):
        if self.states and self.states.strokePositions:
            states = self.states

            device = QOpenGLPaintDevice(self.size)
            painter = QPainter(device)
            painter.beginNativePainting()

            while states.strokePositions:
                p = states.strokePositions.pop(0)
                p = QPointF(p.x(), self.size.height()-p.y())

                g = QRadialGradient(p.x(), p.y(), states.brushSize/2)

                steps = states.brushSize//4
                for i in range(0, steps+1):
                    r = i/steps
                    g.setColorAt(r, states.getBrushColor(r))

                painter.setPen(Qt.NoPen)
                painter.setBrush(g)

                painter.drawEllipse(p, states.brushSize, states.brushSize)

            painter.endNativePainting()
            painter.end()
            self.states = None

class ImageCanvas(QQuickFramebufferObject):
    canvasSizeUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextureFollowsItemSize(False)

        self.textureSize = QSize(0,0)
        self.states = ImageCanvasStates()
        self.last_pos = None

    def createRenderer(self):
        return ImageCanvasRenderer(self, self.textureSize)

    @pyqtProperty(QSize, notify=canvasSizeUpdated)
    def canvasSize(self):
        return self.textureSize
    
    @canvasSize.setter
    def canvasSize(self, size):
        self.textureSize = size

    @pyqtSlot(QPointF)
    def mousePressed(self, position):
        self.states.addStroke(position)
        self.last_pos = position

    @pyqtSlot(QPointF)
    def mouseReleased(self, position):
        self.states.clearStroke()

    @pyqtSlot(QPointF)
    def mouseDragged(self, position):
        if self.last_pos == None:
            self.states.addStroke(position)
            self.last_pos = position
        else:
            last = QPointF(self.last_pos)
            s = self.states.getBrushAbsoluteSpacing()
            v = QPointF(position.x()-last.x(), position.y()-last.y())
            m = (v.x()*v.x() + v.y()*v.y())**0.5
            r = m/s
            if r < 1:
                return
            
            for i in range(1, int(r)+1):
                f = i*s/m
                p = QPointF(last.x()+v.x()*f, last.y()+v.y()*f)
                self.states.addStroke(p)
            self.last_pos = QPointF(p)