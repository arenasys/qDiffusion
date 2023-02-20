from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtQuick import QQuickFramebufferObject
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QPolygonF, QOpenGLPaintDevice, QImage, QRadialGradient
import OpenGL.GL as gl
import copy

from canvas.shared import *

class CanvasRendererLayer():
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

class CanvasRendererState():
    def __init__(self, index, layer, selection):
        self.index = index
        self.data = layer.getImage()
        self.selection = selection.copy()

class CanvasStroke():
    def __init__(self, pos):
        self.position = pos
    
class CanvasRenderer(QQuickFramebufferObject.Renderer):
    def __init__(self, size, maxStates=10):
        super().__init__()
        self.size = size

        self.display = None
        self.buffer = None
        self.layers = []

        self.activeTool = None
        self.activeBrush = None
        self.activeSelection = None
        self.activeLayer = -1

        self.states = []
        self.maxStates = 100
        self.selectionState = None

        self.changes = None

        self.moving = False
        self.movingLayer = -1
        self.movingPosition = QPointF(0,0)
        self.movingOffset = QPointF(0,0)

    def createLayer(self, size):
        fbo = super().createFramebufferObject(size)
        return CanvasRendererLayer(size, fbo)
    
    def createFramebufferObject(self, size):
        self.display = self.createLayer(self.size)
        self.buffer = self.createLayer(self.size)
        self.selection = self.createLayer(self.size)

        self.states = []

        return self.display.fbo
    
    def synchronize(self, canvas):
        canvas.synchronize(self)
        self.changes = canvas.getChanges()

    def render(self):
        if not self.layers:
            return

        self.applySources()

        if self.changes:
            self.applyChanges()

        self.renderDisplay()

    def renderDisplay(self):
        painter = self.display.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        for i, layer in enumerate(self.layers):
            if not layer.visible:
                continue
            layerImage = layer.getImage()
            layerPainter = QPainter(layerImage)
            if i == self.activeLayer:
                layerPainter.setOpacity(self.activeBrush.opacity)
                if self.activeTool == CanvasTool.ERASE:
                    layerPainter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                layerPainter.drawImage(0,0, self.buffer.getImage())
            if i == self.movingLayer:
                layerPainter.drawImage(self.movingPosition + self.movingOffset, self.selection.getImage())
            layerPainter.end()
            painter.setOpacity(layer.opacity)
            painter.drawImage(0,0,layerImage)
            painter.resetTransform()
        self.display.endPaint()
    
    def renderMask(self):
        # opengl backend cant draw self-intersecting polygons
        img = QImage(self.selection.size, QImage.Format_ARGB32_Premultiplied)
        img.fill(0)
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QColor.fromRgbF(1.0, 1.0, 1.0))
        painter.setBrush(QColor.fromRgbF(1.0, 1.0, 1.0))
        for shape in self.changes.selection.shapes:
            if shape.mode == CanvasSelectionMode.SUBTRACT:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
            else:
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            if shape.tool == CanvasTool.RECTANGLE_SELECT:
                painter.drawRect(shape.bound)
            elif shape.tool == CanvasTool.ELLIPSE_SELECT:
                painter.drawEllipse(shape.bound)
            elif shape.tool == CanvasTool.PATH_SELECT and len(shape.bound) >= 3:
                painter.drawPolygon(QPolygonF(shape.bound))
        painter.end()

        painter = self.selection.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        painter.drawImage(0,0,img)
        self.selection.endPaint()

    def applySources(self):
        for layer in self.layers:
            if layer.source:
                painter = layer.beginPaint()
                painter.drawImage(0,0,layer.source)
                layer.endPaint()
                layer.source = None

    def applyChanges(self):
        self.activeLayer = self.changes.layer
        self.activeBrush = self.changes.brush
        self.activeTool = self.changes.tool

        if not self.moving and CanvasOperation.START_MOVE in self.changes.operations:
            self.changes.operations.add(CanvasOperation.SAVE_STATE)

        if CanvasOperation.SAVE_STATE in self.changes.operations:
            if len(self.states) == self.maxStates:
                self.states.pop(0)
            self.states.append(CanvasRendererState(self.activeLayer, self.layers[self.activeLayer], self.changes.selection))

        if CanvasOperation.RESTORE_STATE in self.changes.operations and self.states:
            state = self.states.pop()
            painter = self.layers[state.index].beginPaint()
           
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            painter.drawImage(0,0,state.data)
            self.layers[state.index].endPaint()

            self.selectionState = state.selection
            self.changes.selection = state.selection
            self.changes.operations.add(CanvasOperation.UPDATE_SELECTION)
            self.resetMoving()
            self.moving = False

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
        
        if CanvasOperation.STROKE in self.changes.operations:
            painter = self.layers[self.activeLayer].beginPaint()
            painter.setOpacity(self.activeBrush.opacity)
            if self.activeTool == CanvasTool.ERASE:
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawImage(0,0,self.buffer.getImage())
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            self.layers[self.activeLayer].endPaint()
            self.buffer.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.buffer.endPaint()

        if CanvasOperation.UPDATE_SELECTION in self.changes.operations:
            self.movingOffset = QPointF(0,0)
            self.movingPosition = QPointF(0,0)
            self.renderMask()

        if CanvasOperation.START_MOVE in self.changes.operations and not self.moving:
            painter = self.selection.beginPaint()
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.drawImage(0,0,self.layers[self.activeLayer].getImage())
            self.selection.endPaint()
            painter = self.layers[self.activeLayer].beginPaint()
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawImage(0,0,self.selection.getImage())
            self.layers[self.activeLayer].endPaint()
            
            self.resetMoving()
            self.moving = True
            self.movingLayer = self.activeLayer

        if CanvasOperation.UPDATE_MOVE in self.changes.operations:
            self.movingPosition = self.movingPosition + self.movingOffset
            self.movingOffset = QPointF(0,0)
        else:
            self.movingOffset = self.changes.move

        if CanvasOperation.END_MOVE in self.changes.operations:
            if self.moving:
                selection = QImage(self.selection.getImage())

                painter = self.layers[self.movingLayer].beginPaint()
                painter.drawImage(self.movingPosition + self.movingOffset, selection)
                self.layers[self.movingLayer].endPaint()


                painter = self.selection.beginPaint()
                gl.glClearColor(0, 0, 0, 0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                painter.drawImage(self.movingPosition + self.movingOffset, selection)
                self.selection.endPaint()

                self.resetMoving()
                self.moving = False

    def resetMoving(self):
        self.movingOffset = QPointF(0,0)
        self.movingPosition = QPointF(0,0)
        self.movingLayer = -1