from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, Qt, QPointF, QPoint, QSize, QRectF, QTimer, QByteArray, QBuffer, QIODevice, QMimeData
from PyQt5.QtQuick import QQuickFramebufferObject
from PyQt5.QtGui import QColor, QPainter, QImage, QGuiApplication, QDrag, QPixmap
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType
import math

from canvas.renderer import *
from canvas.shared import *
from misc import MimeData

MIME_LAYER = "application/x-qd-layer"

class CanvasBrush(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor()
        self._size = 100
        self._spacing = 0.1
        self._hardness = 1.0
        self._opacity = 1.0
        self._exclusive = False
        self.setColor(QColor())
        self.updated.emit()

        self._mode = QPainter.CompositionMode_SourceOver
        self._modeValues = [QPainter.CompositionMode_SourceOver, QPainter.CompositionMode_DestinationOut]
        self._modeNames = ["Normal", "Erase"]

    def setColor(self, color):
        self._color = QColor(color)
        self._opacity = self._color.alphaF()
        self._color.setAlphaF(1.0)

    def getAbsoluteSpacing(self):
        return self._size * self._spacing

    def getColor(self, radius):
        hardness = min(self._hardness, 0.99)
        scaledHardness = (hardness + 0.2)/1.2
        alpha = 1.0
        if hardness != 1:
            if hardness >= 0.5:
                h = 1/(scaledHardness) - 1
                alpha = ((math.cos(radius*math.pi)+1)/2)**h
            else:
                h = 1/(1-scaledHardness) - 1
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
        if size != self._size:
            self._size = size
            self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def hardness(self):
        return self._hardness*100
    
    @hardness.setter
    def hardness(self, hardness):
        hardness /= 100
        if hardness != self._hardness:
            self._hardness = hardness
            self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def spacing(self):
        return self._spacing*100
    
    @spacing.setter
    def spacing(self, spacing):
        spacing /= 100
        if spacing != self._spacing:
            self._spacing = spacing
            self.updated.emit()

    @pyqtProperty(float, notify=updated)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, opacity):
        if opacity != self._opacity:
            self._opacity = opacity
            self.updated.emit()

    @pyqtProperty(int, notify=updated)
    def mode(self):
        return self._mode
    
    @pyqtProperty(int, notify=updated)
    def modeIndex(self):
        return self._modeValues.index(self._mode)
    
    @modeIndex.setter
    def modeIndex(self, mode):
        if mode != self._mode:
            self._mode = self._modeValues[mode]
            self.updated.emit()

    @pyqtProperty(list, constant=True)
    def modeNames(self):
        return self._modeNames

class CanvasLayer(QObject):
    updated = pyqtSignal()
    globalKey = 0
    def __init__(self, name, size, parent=None):
        super().__init__(parent)
        self._name = name
        self._thumbnail = QImage()
        self._opacity = 1.0
        self._mode = QPainter.CompositionMode_SourceOver
        self._size = size
        self._visible = True
        self._key = CanvasLayer.globalKey
        self._image = QImage()
        CanvasLayer.globalKey += 1

        self.changed = False
        self.source = None

    def setSource(self, source):
        self.source = source
        self.size = source.size()
        self.changed = True

    def synchronize(self, layer, renderer):
        self._image = QImage(layer.getImage())

        if not self.changed:
            return False
        
        layer.opacity = self._opacity
        layer.visible = self._visible
        layer.mode = self._mode
        if self.source:
            #print("APPLY")
            layer.source = QImage(self.source)
            self.source = None
        self.updated.emit()
        self.changed = False
        return True

    @pyqtProperty(int, notify=updated)
    def key(self):
        return self._key

    @pyqtProperty(str, notify=updated)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.changed = True

    @pyqtProperty(float, notify=updated)
    def opacity(self):
        return self._opacity*100

    @opacity.setter
    def opacity(self, opacity):
        opacity /= 100
        if opacity != self._opacity:
            self._opacity = opacity
            self.updated.emit()
            self.changed = True

    @pyqtProperty(bool, notify=updated)
    def visible(self):
        if self._opacity == 0.0:
            return False
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        self.changed = True
    
    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image

class Canvas(QQuickFramebufferObject):
    sourceUpdated = pyqtSignal()
    layersUpdated = pyqtSignal()
    toolUpdated = pyqtSignal()
    needsUpdated = pyqtSignal()
    colorSampled = pyqtSignal(QColor)
    changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextureFollowsItemSize(False)
        self.setMirrorVertically(True)
        self.setup()

        self._tool = CanvasTool.BRUSH
        self._brush = CanvasBrush()
        self._firstSetup = True

    def setup(self):
        self._source = ""
        self._sourceSize = QSize(1,1)

        self._layers = {} # key -> layer
        self._layersOrder = [] # index -> key
        self._activeLayer = -1

        self.changes = CanvasChanges()
        self.lastMousePosition = None

        self.thumbnailsNeedUpdate = False

        self._toolStart = None
        self._toolActive = False

        self._needsUpdate = False
        self._setup = True
        self._display = None
        self._painting = False

        self.sourceUpdated.emit()
        self.layersUpdated.emit()
        self.toolUpdated.emit()

    def getChanges(self):
        changes = self.changes
        changes.brush = self._brush
        changes.tool = self._tool
        changes.layer = self._activeLayer
        self.changes = CanvasChanges()
        return changes

    def synchronize(self, renderer):
        if renderer.display == None or self._sourceSize == QSize(0,0):
            return False

        if self._setup:
            renderer.setup(self._sourceSize)
            self.update()
            self._setup = False
            return False

        if renderer.changed or not self._display:
            self._display = renderer.display.getImage()

        if renderer.changed:
            self.changed.emit()
            renderer.changed = False

        self.synchronizeLayers(renderer)
        
        self._needsUpdate = False

        if renderer.sample:
            self.colorSampled.emit(renderer.sample)
            renderer.sample = None

        return True

    def synchronizeLayers(self, renderer):
        if renderer.layersOrder != self._layersOrder:
            renderer.changed = True
        renderer.layersOrder = self._layersOrder
        for key in renderer.layersOrder:
            if not key in renderer.layers:
                renderer.layers[key] = renderer.createBuffer(self._layers[key]._size)
                self.layersUpdated.emit()
            self._layers[key].synchronize(renderer.layers[key], renderer)

    def moveLayer(self, source, destination):
        key = self._layersOrder.pop(source)
        if source < destination:
            destination -= 1
        self._layersOrder.insert(destination, key)

        self.layersUpdated.emit()

    def insertLayer(self, index, source):
        idx = len(self._layersOrder) + 1
        layer = CanvasLayer(f"{idx}", self._sourceSize, self)
        layer.setSource(source)
        self._layers[layer.key] = layer
        if index == -1:
            self._layersOrder.append(layer.key)
        else:
            self._layersOrder.insert(index, layer.key)
        self.changes.operations.add(CanvasOperation.LOAD)
        self.layersUpdated.emit()
        return layer.key

    @pyqtProperty(bool, notify=needsUpdated)
    def needsUpdate(self):
        return self._needsUpdate
    
    def requestUpdate(self):
        self._needsUpdate = True
        self.needsUpdated.emit()

    def createRenderer(self):
        #print("CREATE CANVAS", self._sourceSize)
        return CanvasRenderer(self._sourceSize)

    @pyqtProperty(list, notify=layersUpdated)
    def layers(self):
        return [self._layers[key] for key in self._layersOrder]

    @pyqtProperty(int, notify=layersUpdated)
    def activeLayer(self):
        if self._activeLayer == -1:
            return -1
        return self._layersOrder.index(self._activeLayer)

    @activeLayer.setter
    def activeLayer(self, layer):
        self._activeLayer = self._layersOrder[layer]
        self.layersUpdated.emit()

    @pyqtProperty(QSize, notify=sourceUpdated)
    def sourceSize(self):
        return self._sourceSize
    
    @pyqtProperty(CanvasBrush, notify=toolUpdated)
    def brush(self):
        return self._brush

    @pyqtSlot(QImage, QSize)
    def setupPainting(self, base, paint=None):
        self.setup()
        self._painting = True

        self._sourceSize = base.size()
        self.sourceUpdated.emit()
        self._layers = {}
        self._layersOrder = []

        self.insertLayer(0, base)
        self._activeLayer = self.insertLayer(1, paint or QImage())
        self.layersUpdated.emit()

        self._brush._exclusive = False

        self.changes = CanvasChanges()
        self.changes.operations.add(CanvasOperation.LOAD)
        self.changes.reset = True

    @pyqtSlot(QImage, QSize)
    def setupMask(self, image, size):
        self._painting = False
        self.setup()
        if image.size() != size:
            image = image.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            dx = int((image.width()-size.width())//2)
            dy = int((image.height()-size.height())//2)
            image = image.copy(dx, dy, size.width(), size.height())

        self._sourceSize = image.size()
        self.sourceUpdated.emit()
        self._layers = {}
        self._layersOrder = []
        self._activeLayer = self.insertLayer(0, image)
        self.layersUpdated.emit()

        self._brush.setColor(Qt.white)
        self._brush._exclusive = True

        self.changes = CanvasChanges()
        self.changes.operations.add(CanvasOperation.LOAD)
        self.changes.reset = True

    @pyqtSlot(int, list, QSize)
    def setupSubprompt(self, count, areas, size):
        self._painting = False
        self.setup()
        for i in range(len(areas)):
            if areas[i].size() != size:
                image = areas[i].scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                dx = int((image.width()-size.width())//2)
                dy = int((image.height()-size.height())//2)
                areas[i] = image.copy(dx, dy, size.width(), size.height())
        
        self._sourceSize = size
        self.sourceUpdated.emit()
        self._layers = {}
        self._layersOrder = []

        self.syncSubprompt(count, 0, areas)

        self.changes = CanvasChanges()
        self.changes.operations.add(CanvasOperation.LOAD)
        self.changes.reset = True

    @pyqtSlot(int, int, list)
    def syncSubprompt(self, count, active, areas):
        size = self._sourceSize
        for i in range(len(areas)):
            if areas[i].size() != size:
                image = areas[i].scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                dx = int((image.width()-size.width())//2)
                dy = int((image.height()-size.height())//2)
                areas[i] = image.copy(dx, dy, size.width(), size.height())

        layerCount = len(self._layersOrder)
        if count < layerCount:
            self._layersOrder = self._layersOrder[:count]
        elif count > layerCount:
            for i in range(layerCount, count):
                if i < len(areas):
                    self.insertLayer(-1, areas[i])
                else:
                    self.insertLayer(-1, QImage())
        
        if not count:
            self._brush.setColor(Qt.white)
        else:
            self._activeLayer = self._layersOrder[active]
            self._brush.setColor(QColor.fromHsvF(active/4, 0.7, 0.7, 1.0))
        self._brush._exclusive = True

    @pyqtSlot(result=bool)
    def forceSync(self):
        if self._toolActive:
            if self._tool in {CanvasTool.BRUSH, CanvasTool.ERASE}:
                self.requestUpdate()
                self.changes.operations.add(CanvasOperation.STROKE)
                self._toolActive = False
                return True
        return False

    def getLayer(self, position):
        return self._layers[self._layersOrder[position]]

    def transformMousePosition(self, pos):
        if not self._sourceSize.width():
            return pos
        factor =  self.width()/self._sourceSize.width()
        offset = QPointF(self.x(), self.y())
        return (pos - offset) / factor

    @pyqtSlot(QPointF, int)
    def mousePressed(self, position, modifiers):
        self.requestUpdate()
        position = self.transformMousePosition(position)
        self._toolStart = position
        self._toolActive = True

        op = CanvasOperation.SAMPLE_COLOR if (modifiers & Qt.ControlModifier) else CanvasOperation.UPDATE_STROKE

        if self._tool in {CanvasTool.BRUSH, CanvasTool.ERASE}:
            self.changes.strokes.append(position)
            self.lastMousePosition = position
            self.changes.operations.add(op)

    @pyqtSlot(QPointF, int)
    def mouseReleased(self, position, modifiers):
        self.requestUpdate()
        self._toolActive = False

        if self._tool in {CanvasTool.BRUSH, CanvasTool.ERASE}:
            self.changes.operations.add(CanvasOperation.STROKE)
            
        return

    @pyqtSlot(QPointF, int)
    def mouseDragged(self, position, modifiers):
        self.requestUpdate()
        position = self.transformMousePosition(position)

        if self._tool in {CanvasTool.BRUSH, CanvasTool.ERASE}:
            if self.lastMousePosition == None:
                self.changes.strokes.append(position)
                self.lastMousePositions = position
            else:
                last = QPointF(self.lastMousePosition)
                s = self._brush.getAbsoluteSpacing()
                v = QPointF(position.x()-last.x(), position.y()-last.y())
                m = (v.x()*v.x() + v.y()*v.y())**0.5
                r = m/s
                if r < 1 or not r:
                    return
                
                for i in range(1, int(r)+1):
                    f = i*s/m
                    p = QPointF(last.x()+v.x()*f, last.y()+v.y()*f)
                    self.changes.strokes.append(p)
                self.lastMousePosition = QPointF(p)
            
            self.changes.operations.add(CanvasOperation.UPDATE_STROKE)
 
    @pyqtSlot(result=QImage)
    def getImage(self):
        return self._layers[self._activeLayer].image
    
    @pyqtSlot(result=list)
    def getImages(self):
        return [self._layers[i].image for i in self._layersOrder]
    
    @pyqtSlot(result=QImage)
    def getDisplay(self):
        return self._display
    
    @pyqtProperty(CanvasWrapper, notify=sourceUpdated)
    def wrapper(self):
        return CanvasWrapper(self)

def registerTypes():
    qmlRegisterType(Canvas, "gui", 1, 0, "AdvancedCanvas")
    qmlRegisterUncreatableType(CanvasBrush, "gui", 1, 0, "CanvasBrush", "Not a QML type")
    qmlRegisterUncreatableType(CanvasLayer, "gui", 1, 0, "CanvasLayer", "Not a QML type")
    qmlRegisterUncreatableType(CanvasWrapper, "gui", 1, 0, "CanvasWrapper", "Not a QML type")