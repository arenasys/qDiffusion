from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF
from PyQt5.QtQuick import QQuickFramebufferObject
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QPolygonF, QOpenGLPaintDevice, QImage, QRadialGradient, QGuiApplication
import OpenGL.GL as gl
import copy
import time

#import cv2
#import numpy as np
#np.seterr("ignore")

from canvas.shared import *

class CanvasRendererBuffer():
    def __init__(self, size, buffer):
        self.buffer = buffer
        self.size = size
        self.opacity = 1.0
        self.visible = True
        self.source = None
        self.cached = None

        self.initial = True

    def initialize(self):
        if self.initial:
            self.initial = False
            self.buffer.bind()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def getImage(self):
        if self.cached == None:
            self.cached = self.buffer.toImage()
        return self.cached

    def getThumbnail(self, size=128):
        img = self.getImage().scaledToWidth(size, mode=Qt.SmoothTransformation)
        return img

    def beginPaint(self):
        self.buffer.bind()
        self.cached = None
        self.device = QOpenGLPaintDevice(self.size)
        self.painter = QPainter(self.device)
        self.painter.beginNativePainting()
        return self.painter
    
    def endPaint(self):
        self.painter.endNativePainting()
        self.painter.end()
        self.device = None
    
class CanvasRenderer(QQuickFramebufferObject.Renderer):
    def __init__(self, size):
        super().__init__()
        self.changes = None
        self.display = None
        self.buffer = None
        self.size = None
        self.setup(size)
    
    def setup(self, size):
        if self.size and self.size != size:
            self.invalidateFramebufferObject()

        self.size = size

        self.layers = {}
        self.layersOrder = []

        self.activeTool = None
        self.activeBrush = None
        self.activeSelection = None
        self.activeLayer = -1

        self.changed = False
        self.sample = None

    def createBuffer(self, size):
        buffer = super().createFramebufferObject(size)
        return CanvasRendererBuffer(size, buffer)
    
    def resizeBuffer(self, buffer, newSize):
        newBuffer = super().createFramebufferObject(newSize)
        oldBuffer = buffer.buffer
        buffer.buffer = newBuffer
        buffer.size = newSize

        painter = buffer.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        painter.drawImage(0,0,oldBuffer.toImage())
        buffer.endPaint()
    
    def getLayer(self, key):
        return self.layers[key]
        
    def createFramebufferObject(self, size):
        #print("CREATE", self.size)
        self.display = self.createBuffer(self.size)
        self.buffer = self.createBuffer(self.size)

        self.states = []

        return self.display.buffer
    
    def synchronize(self, canvas):
        if canvas.synchronize(self):
            self.changes = canvas.getChanges()

    def render(self):
        if not self.size or self.size.width() == 1:
            return
        
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.display.initialize()
        self.buffer.initialize()
        for key in self.layers:
            self.layers[key].initialize()

        if not self.layersOrder or not self.display:
            return

        if self.changes.operations:
            self.applyOperations()

        self.renderDisplay()

        if CanvasOperation.SAMPLE_COLOR in self.changes.operations and self.changes.strokes:
            point = self.changes.strokes[-1].toPoint()
            if point.x() >= 0 and point.x() < self.size.width() and point.y() >= 0 and point.y() < self.size.height():
                self.sample = self.display.getImage().pixelColor(point)

    def renderDisplay(self):
        painter = self.display.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        for key in self.layersOrder:
            layer = self.layers[key]
            if not layer.visible:
                continue
            layerImage = layer.getImage()

            if key == self.activeLayer and not self.activeBrush._exclusive:
                layerImage = QImage(layerImage)
                layerPainter = QPainter(layerImage)
                layerPainter.setOpacity(self.activeBrush.opacity)
                layerPainter.setCompositionMode(self.activeBrush.mode)
                layerPainter.drawImage(0, 0, self.buffer.getImage())
                layerPainter.end()
            
            painter.drawImage(0,0,layerImage)

        if self.activeBrush._exclusive:
            painter.setCompositionMode(self.activeBrush.mode)
            painter.drawImage(0,0,self.buffer.getImage())

        self.display.endPaint()

    def applySources(self):
        for key in self.layersOrder:
            layer = self.layers[key]
            if layer.source:
                painter = layer.beginPaint()
                painter.drawImage(0,0,layer.source)
                layer.endPaint()
                layer.source = None

    def applyOperations(self):
        self.activeLayer = self.changes.layer
        self.activeBrush = self.changes.brush
        self.activeTool = self.changes.tool
        
        if CanvasOperation.LOAD in self.changes.operations:
            self.applySources()

        if CanvasOperation.UPDATE_STROKE in self.changes.operations and self.changes.strokes:
            painter = self.buffer.beginPaint()
            brush = self.activeBrush
            
            while self.changes.strokes:
                p = self.changes.strokes.pop(0)

                gradient = QRadialGradient(p.x(), p.y(), brush.size/2)

                steps = max(int(brush.size//4), 3)
                for i in range(0, steps+1):
                    r = i/steps                   
                    if r == 1.0:
                        c =  brush.getColor(r)
                        gradient.setColorAt(0.999,c)
                        c.setAlphaF(0.0)
                        gradient.setColorAt(1.0, c)
                    else:
                        gradient.setColorAt(r, brush.getColor(r))


                painter.setPen(Qt.NoPen)
                painter.setBrush(gradient)

                painter.drawEllipse(p, brush.size, brush.size)

            self.buffer.endPaint()
        
        if CanvasOperation.STROKE in self.changes.operations:
            if self.activeBrush._exclusive: # HACK for subprompts
                if self.activeBrush._mode == QPainter.CompositionMode_DestinationOut:
                    for key in self.layersOrder:
                        painter = self.layers[key].beginPaint()
                        painter.setOpacity(self.activeBrush.opacity)
                        painter.setCompositionMode(self.activeBrush.mode)
                        painter.drawImage(0,0,self.buffer.getImage())
                        self.layers[key].endPaint()
                else:
                    for key in self.layersOrder:
                        if key == self.activeLayer:
                            mode = self.activeBrush.mode
                        else:
                            mode = QPainter.CompositionMode_DestinationOut
                        painter = self.layers[key].beginPaint()
                        painter.setOpacity(self.activeBrush.opacity)
                        painter.setCompositionMode(mode)
                        painter.drawImage(0,0,self.buffer.getImage())
                        self.layers[key].endPaint()
            else:
                painter = self.layers[self.activeLayer].beginPaint()
                painter.setOpacity(self.activeBrush.opacity)
                painter.setCompositionMode(self.activeBrush.mode)
                painter.drawImage(0,0,self.buffer.getImage())
                self.layers[self.activeLayer].endPaint()
            
            self.buffer.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.buffer.endPaint()
            self.changed = True