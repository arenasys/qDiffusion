from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, Qt, QPointF, QSize, QRect, QTimer, QEvent
from PyQt5.QtQuick import QQuickFramebufferObject,  QQuickPaintedItem, QQuickItem
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QOpenGLPaintDevice, QImage, QConicalGradient, QRadialGradient, QMouseEvent
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType
import math
import OpenGL.GL as gl
from enum import Enum

class CanvasLayer():
    def __init__(self, size, fbo):
        self.fbo = fbo
        self.size = size
        self.changed = True
        self.opacity = 1.0
        self.visible = True
        self.source = None
    
    def getImage(self):
        return self.fbo.toImage()

    def getThumbnail(self, size=128):
        self.changed = False
        return self.getImage().scaledToWidth(size, mode=Qt.SmoothTransformation)

    def beginPaint(self):
        self.fbo.bind()
        self.device = QOpenGLPaintDevice(self.size)
        self.painter = QPainter(self.device)
        self.painter.beginNativePainting()
        return self.painter
    
    def endPaint(self):
        self.painter.endNativePainting()
        self.painter.end()
        self.device = None
        self.changed = True

class CanvasState():
    def __init__(self, index, layer):
        self.index = index
        self.data = layer.getImage()

class CanvasStroke():
    def __init__(self, pos):
        self.position = pos

class CanvasOperation(Enum):
    STROKE = 1
    SAVE_STATE = 2
    RESTORE_STATE = 3
    UPDATE = 4

class CanvasChanges():
    def __init__(self):
        self.reset = False
        self.layer = 1
        self.tool = EditorTool.ERASE
        self.brush = None
        self.strokes = []

        self.operations = set()
    
class Canvas(QQuickFramebufferObject.Renderer):
    def __init__(self, size, maxStates=10):
        super().__init__()
        self.size = size

        self.display = None
        self.buffer = None
        self.layers = []

        self.activeTool = None
        self.activeBrush = None
        self.activeLayer = -1

        self.states = []
        self.maxStates = 100

        self.changes = None
        self.changed = False

    def createLayer(self, size):
        fbo = super().createFramebufferObject(size)
        return CanvasLayer(size, fbo)
    
    def createFramebufferObject(self, size):
        self.display = self.createLayer(self.size)
        self.buffer = self.createLayer(self.size)

        self.states = []

        return self.display.fbo
    
    def synchronize(self, canvas):
        canvas.synchronize(self)
        self.changes = canvas.getChanges()

    def render(self):
        self.changed = False

        if not self.layers:
            return

        for layer in self.layers:
            if layer.source:
                painter = layer.beginPaint()
                painter.drawImage(0,0,layer.source)
                layer.endPaint()
                layer.source = None
                self.changed = True

        if self.changes:
            self.applyChanges()

        if self.changed:
            painter = self.display.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            for i, layer in enumerate(self.layers):
                if not layer.visible:
                    continue
                layerImage = layer.getImage()
                if i == self.activeLayer:
                    layerPainter = QPainter(layerImage)
                    layerPainter.setOpacity(self.activeBrush.opacity)
                    if self.activeTool == EditorTool.ERASE:
                        layerPainter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                    layerPainter.drawImage(0,0, self.buffer.getImage())
                    layerPainter.end()
                painter.setOpacity(layer.opacity)
                painter.drawImage(0,0,layerImage)
            self.display.endPaint()

    def applyChanges(self):
        self.activeLayer = self.changes.layer
        self.activeBrush = self.changes.brush
        self.activeTool = self.changes.tool

        if CanvasOperation.SAVE_STATE in self.changes.operations:
            if len(self.states) == self.maxStates:
                self.states.pop(0)
            self.states.append(CanvasState(self.activeLayer, self.layers[self.activeLayer]))

        if CanvasOperation.RESTORE_STATE in self.changes.operations and self.states:
            state = self.states.pop()
            painter = self.layers[state.index].beginPaint()
           
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            painter.drawImage(0,0,state.data)
            self.layers[state.index].endPaint()
            self.changed = True

        if self.changes.strokes:
            painter = self.buffer.beginPaint()
            brush = self.activeBrush
            
            while self.changes.strokes:
                p = self.changes.strokes.pop(0).position

                gradient = QRadialGradient(p.x(), p.y(), brush.size/2)

                steps = brush.size//4
                for i in range(0, steps+1):
                    r = i/steps
                    gradient.setColorAt(r, brush.getColor(r))

                painter.setPen(Qt.NoPen)
                painter.setBrush(gradient)

                painter.drawEllipse(p, brush.size, brush.size)

            self.buffer.endPaint()
            self.changed = True
        
        if CanvasOperation.STROKE in self.changes.operations:
            painter = self.layers[self.activeLayer].beginPaint()
            painter.setOpacity(self.activeBrush.opacity)
            if self.activeTool == EditorTool.ERASE:
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawImage(0,0,self.buffer.getImage())
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            self.layers[self.activeLayer].endPaint()
            self.buffer.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.buffer.endPaint()

        if CanvasOperation.UPDATE in self.changes.operations:
            self.changed = True


class EditorBrush(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor()
        self._size = 20
        self._spacing = 0.1
        self._hardness = 0.5
        self._opacity = 1.0
        self.setColor(QColor())
        self.updated.emit()

    def setColor(self, color):
        self._color = QColor(color)
        self._opacity = self._color.alphaF()
        self._color.setAlphaF(1.0)

    def getAbsoluteSpacing(self):
        return self._size * self._spacing

    def getColor(self, radius):
        hardness = (self._hardness + 0.2)/1.2
        alpha = 1.0
        if self._hardness != 1:
            if self._hardness >= 0.5:
                h = 1/(hardness) - 1
                alpha = ((math.cos(radius*math.pi)+1)/2)**h
            else:
                h = 1/(1-hardness) - 1
                alpha = 1-(((math.cos((radius+1)*math.pi)+1)/2))**h

        color = QColor(self._color)
        color.setAlphaF(alpha)
        return color

    @pyqtProperty(QColor, notify=updated)
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color):
        self.setColor(color)
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def size(self):
        return self._size
    
    @size.setter
    def size(self, size):
        self._size = size
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def hardness(self):
        return self._hardness
    
    @hardness.setter
    def hardness(self, hardness):
        self._hardness = hardness
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def spacing(self):
        return self._spacing
    
    @spacing.setter
    def spacing(self, spacing):
        self._spacing = spacing
        self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self.updated.emit()

class EditorLayer(QObject):
    updated = pyqtSignal()
    def __init__(self, size, parent=None):
        super().__init__(parent)
        self._name = "Layer"
        self._thumbnail = QImage()
        self._opacity = 1.0
        self._mode = QPainter.CompositionMode_SourceOver
        self._size = size
        self._visible = True

        self.changed = False
        self.source = None

    def setSource(self, source):
        self.source = source
        self.size = source.size()
        self.changed = True

    def synchronize(self, layer, updateThumbnail=False):
        if updateThumbnail and layer.changed:
            self._thumbnail = QImage(layer.getThumbnail())
            self.updated.emit()

        if not self.changed:
            return False

        layer.opacity = self._opacity
        layer.visible = self._visible
        layer.mode = self._mode
        if self.source:
            layer.source = QImage(self.source)
            self.source = None
        self.updated.emit()
        self.changed = False
        return True

    @pyqtProperty(str, notify=updated)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.changed = True

    @pyqtProperty(float, notify=updated)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self.changed = True

    @pyqtProperty(bool, notify=updated)
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        self.changed = True

    @pyqtProperty(QImage, notify=updated)
    def thumbnail(self):
        return self._thumbnail

class EditorTool(Enum):
    BRUSH = 1
    ERASE = 2

class Editor(QQuickFramebufferObject):
    sourceUpdated = pyqtSignal()
    layersUpdated = pyqtSignal()
    brushUpdated = pyqtSignal()
    toolUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextureFollowsItemSize(False)
        self.setMirrorVertically(True)

        self._source = ""
        self._sourceSize = QSize(0,0)
        self._tool = EditorTool.BRUSH
        self._brush = EditorBrush()
        self._layers = []
        self._activeLayer = -1

        self.changes = CanvasChanges()
        self.lastMousePosition = None

        self.thumbnailTimer = QTimer(self)
        self.thumbnailTimer.timeout.connect(self.updateThumbnails)
        self.thumbnailTimer.start(250)
        self.thumbnailsUpdate = False

    def getChanges(self):
        changes = self.changes
        changes.brush = self._brush
        changes.tool = self._tool
        changes.layer = self._activeLayer
        self.changes = CanvasChanges()
        return changes

    def synchronize(self, renderer):
        self.synchronizeLayers(renderer)

    def synchronizeLayers(self, renderer):
        if self.changes.reset:
            renderer.layers = [renderer.createLayer(layer._size) for layer in self._layers]
            self.layersUpdated.emit()

        for i, layer in enumerate(self._layers):
            if layer.synchronize(renderer.layers[i], self.thumbnailsUpdate):
                self.changes.operations.add(CanvasOperation.UPDATE)
        self.thumbnailsUpdate = self.changes.reset

    @pyqtSlot()
    def updateThumbnails(self):
        self.thumbnailsUpdate = True

    def createRenderer(self):
        return Canvas(self._sourceSize)

    @pyqtProperty(list, notify=layersUpdated)
    def layers(self):
        return self._layers

    @pyqtProperty(int, notify=layersUpdated)
    def activeLayer(self):
        return self._activeLayer

    @activeLayer.setter
    def activeLayer(self, layer):
        self._activeLayer = layer
        self.layersUpdated.emit()

    @pyqtProperty(str, notify=sourceUpdated)
    def source(self):
        return self._source

    @source.setter
    def source(self, path):
        self._source = path
        self.sourceUpdated.emit()

    @pyqtProperty(QSize, notify=sourceUpdated)
    def sourceSize(self):
        return self._sourceSize

    @pyqtSlot()
    def load(self):
        source = QImage(self._source)
        self._sourceSize = source.size()
        self.sourceUpdated.emit()
        self._layers = [EditorLayer(source.size(), self), EditorLayer(source.size(), self)]
        self._layers[0].setSource(source)
        self._activeLayer = 0
        self.changes = CanvasChanges()
        self.changes.reset = True

    def addStroke(self, position):
        self.changes.strokes.append(CanvasStroke(position))

    @pyqtSlot(QPointF)
    def mousePressed(self, position):
        self.changes.operations.add(CanvasOperation.SAVE_STATE)
        self.addStroke(position)
        self.lastMousePosition = position

    @pyqtSlot(QPointF)
    def mouseReleased(self, position):
        self.changes.operations.add(CanvasOperation.STROKE)
        return

    @pyqtSlot(QPointF)
    def mouseDragged(self, position):
        if self.lastMousePosition == None:
            self.addStroke(position)
            self.lastMousePositions = position
        else:
            last = QPointF(self.lastMousePosition)
            s = self._brush.getAbsoluteSpacing()
            v = QPointF(position.x()-last.x(), position.y()-last.y())
            m = (v.x()*v.x() + v.y()*v.y())**0.5
            r = m/s
            if r < 1:
                return
            
            for i in range(1, int(r)+1):
                f = i*s/m
                p = QPointF(last.x()+v.x()*f, last.y()+v.y()*f)
                self.addStroke(p)
            self.lastMousePosition = QPointF(p)

    @pyqtSlot()
    def undo(self):
        self.changes.operations.add(CanvasOperation.RESTORE_STATE)

    @pyqtProperty(EditorBrush, notify=brushUpdated)
    def brush(self):
        return self._brush

    @pyqtProperty(int, notify=toolUpdated)
    def tool(self):
        return self._tool.value

    @tool.setter
    def tool(self, tool):
        self._tool = EditorTool(tool)
        self.toolUpdated.emit()
    
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
        self._lightness = 0.5
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

def registerTypes():
    qmlRegisterType(Editor, "gui", 1, 0, "ImageEditor")
    qmlRegisterUncreatableType(EditorBrush, "gui", 1, 0, "ImageEditorBrush", "Not a QML type")
    qmlRegisterUncreatableType(EditorLayer, "gui", 1, 0, "ImageEditorLayer", "Not a QML type")
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(ColorRadial, "gui", 1, 0, "ColorRadial")