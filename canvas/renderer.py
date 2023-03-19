from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF
from PyQt5.QtQuick import QQuickFramebufferObject
from PyQt5.QtGui import QRadialGradient, QColor, QPainter, QPolygonF, QOpenGLPaintDevice, QImage, QRadialGradient, QGuiApplication
import OpenGL.GL as gl
import copy
import time

import cv2
import numpy as np
np.seterr("ignore")

from canvas.shared import *

class CanvasRendererCheckpoint():
    def __init__(self, active, order, layers, selection, mask, floating, floatingPosition, floatingLayer):
        self.active = active
        self.order = copy.copy(order)
        self.restore = {key:layers[key].getImage() for key in layers}
        self.mask = mask.getImage()
        self.selection = selection.copy()
        self.time = time.time()

        self.floating = floating
        self.floatingPosition = floatingPosition
        self.floatingLayer = floatingLayer

class CanvasRendererBuffer():
    def __init__(self, size, buffer):
        self.buffer = buffer
        self.size = size
        self.opacity = 1.0
        self.visible = True
        self.source = None
        self.cached = None

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
        self.mask = None
        self.size = None
        self.setup(size)
    
    def setup(self, size):
        if self.size and self.size != size:
            print("INVALIDATE")
            self.invalidateFramebufferObject()

        self.size = size

        self.layers = {}
        self.layersOrder = []

        self.activeTool = None
        self.activeBrush = None
        self.activeSelection = None
        self.activeLayer = -1

        self.checkpoints = []
        self.maxCheckpoints = 100
        self.atCheckpoint = True

        self.restored = False
        self.restoredSelection = None
        self.restoredActive = None
        self.restoredOrder = None

        self.floating = False
        self.floatingLayer = -1
        self.floatingPosition = QPointF(0,0)
        self.floatingOffset = QPointF(0,0)

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
    
    def getMaskedBuffer(self):
        buffer = self.buffer.getImage()
        painter = QPainter()
        painter.begin(buffer)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawImage(0,0,self.mask.getImage())
        painter.end()
        return buffer

    def makeCheckpoint(self):
        return CanvasRendererCheckpoint(self.activeLayer, self.layersOrder, self.layers, self.changes.selection, self.mask, 
                                        self.floating, self.floatingPosition, self.floatingLayer)

    def restoreCheckpoint(self, checkpoint):
        self.layersOrder = checkpoint.order
        self.activeLayer = checkpoint.active
        self.changes.selection = checkpoint.selection
        key = self.activeLayer

        if not key in self.layers:
            self.layers[key] = self.createBuffer(self.size)
        
        for key in self.layers:
            if key in checkpoint.restore:
                painter = self.layers[key].beginPaint()
                gl.glClearColor(0, 0, 0, 0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                painter.drawImage(0,0,checkpoint.restore[key])
                self.layers[key].endPaint()

        if self.floatingLayer != -1:
            self.getLayer(self.floatingLayer).changed = True

        self.floating = checkpoint.floating
        self.floatingLayer = checkpoint.floatingLayer
        self.floatingPosition = checkpoint.floatingPosition
        self.floatingOffset = QPointF(0,0)

        if self.floating:
            painter = self.mask.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            painter.drawImage(0,0,checkpoint.mask)
            self.mask.endPaint()
        else:
            self.changes.selection.clear()
            self.renderMask()

        if self.floatingLayer != -1:
            self.getLayer(self.floatingLayer).changed = True

        self.restored = True
        self.restoredActive = self.activeLayer
        self.restoredSelection = self.changes.selection
        self.restoredOrder =self.layersOrder
        
    def createFramebufferObject(self, size):
        print("CREATE", self.size)
        self.display = self.createBuffer(self.size)
        self.buffer = self.createBuffer(self.size)
        self.mask = self.createBuffer(self.size)

        self.states = []

        return self.display.buffer
    
    def synchronize(self, canvas):
        if canvas.synchronize(self):
            self.changes = canvas.getChanges()

    def render(self):
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        if not self.layersOrder or not self.display:
            return

        if self.changes.operations:
            self.applyOperations()

        self.renderDisplay()

    def renderDisplay(self):
        painter = self.display.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        for key in self.layersOrder:
            layer = self.layers[key]
            if not layer.visible:
                continue
            layerImage = layer.getImage()

            if key == self.activeLayer or key == self.floatingLayer:
                layerImage = QImage(layerImage)
                layerPainter = QPainter(layerImage)
                if key == self.activeLayer:
                    layerPainter.setOpacity(self.activeBrush.opacity)
                    layerPainter.setCompositionMode(self.activeBrush.mode)
                    layerPainter.drawImage(0,0,self.getMaskedBuffer())
                if key == self.floatingLayer:
                    layerPainter.drawImage(alignQPointF(self.floatingPosition + self.floatingOffset), self.mask.getImage())
                layerPainter.end()
            
            painter.setOpacity(layer.opacity)
            painter.drawImage(0,0,layerImage)

        self.display.endPaint()

    def renderMask(self):
        if self.mask.size != self.size:
            self.resizeBuffer(self.mask, self.size)

        # opengl backend cant draw self-intersecting polygons
        img = QImage(self.mask.size, QImage.Format_ARGB32_Premultiplied)
        img.fill(0)
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QColor.fromRgbF(1.0, 1.0, 1.0))
        painter.setBrush(QColor.fromRgbF(1.0, 1.0, 1.0))
        mask = self.changes.selection.mask
        if not mask.isNull():
            painter.drawImage(0,0,mask)
        shapes = self.changes.selection.shapes
        if shapes:
            for shape in shapes:
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
        else:
            painter.drawRect(QRectF(0, 0, img.width(),img.height()))
        painter.end()

        painter = self.mask.beginPaint()
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        painter.drawImage(0,0,img)
        self.mask.endPaint()

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

        save = False
        save = save or (CanvasOperation.STROKE in self.changes.operations)
        save = save or (CanvasOperation.CUT in self.changes.operations)
        save = save or (CanvasOperation.DELETE in self.changes.operations)
        save = save or (CanvasOperation.PASTE in self.changes.operations)
        save = save or (CanvasOperation.LOAD in self.changes.operations)
        save = save or (CanvasOperation.MOVE in self.changes.operations)

        if CanvasOperation.LOAD in self.changes.operations:
            print("LOAD")
            self.applySources()

        if CanvasOperation.UNDO in self.changes.operations:
            if self.checkpoints:
                if self.atCheckpoint and len(self.checkpoints) > 1:
                    self.restoreCheckpoint(self.checkpoints.pop())
                checkpoint = self.checkpoints[-1]
                if len(self.checkpoints) > 1:
                    self.checkpoints.pop()
                self.restoreCheckpoint(checkpoint)

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
            painter = self.getLayer(self.activeLayer).beginPaint()
            painter.setOpacity(self.activeBrush.opacity)
            painter.setCompositionMode(self.activeBrush.mode)
            painter.drawImage(0,0,self.getMaskedBuffer())
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            self.getLayer(self.activeLayer).endPaint()
            
            self.buffer.beginPaint()
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.buffer.endPaint()

        if CanvasOperation.SET_SELECTION in self.changes.operations:
            self.floatingOffset = QPointF(0,0)
            self.floatingPosition = QPointF(0,0)
            self.renderMask()

        if CanvasOperation.PASTE in self.changes.operations and self.changes.paste:
            image = self.changes.paste

            if self.mask.size.width() < image.size().width() or self.mask.size.height() < image.size().height():
                self.resizeBuffer(self.mask, image.size())

            pasteSize = QPointF(image.size().width(), image.size().height())
            layerCenter = QPointF(self.mask.size.width(), self.mask.size.height()) / 2
            selectionCenter = self.changes.selection.center()

            if selectionCenter:
                offset = selectionCenter - pasteSize / 2
            else:
                offset = layerCenter - pasteSize / 2

            offset = alignQPointF(offset)

            painter = self.mask.beginPaint()
            gl.glClearColor(0,0,0,0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            painter.drawImage(0,0,image)
            self.mask.endPaint()
            self.restoredSelection = self.changes.selection.copy()
            self.restoredSelection.clear()
            self.restoredSelection.setMask(self.convertMask(image))
            self.changes.selection = self.restoredSelection

            self.resetMoving()
            self.floating = True
            self.floatingLayer = self.activeLayer
            self.floatingPosition = offset
            self.getLayer(self.floatingLayer).changed = True

        if CanvasOperation.COPY in self.changes.operations or CanvasOperation.CUT in self.changes.operations:
            mask = self.mask.getImage()
            selection = QImage(mask)

            bound = self.changes.selection.boundingRect()
            if not bound:
                bound = QRectF(QPointF(0, 0), QSizeF(selection.size()))

            bound.translate(-(self.floatingPosition + self.floatingOffset))

            if not self.floating:
                painter = QPainter()
                painter.begin(selection)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.drawImage(0,0,self.getLayer(self.activeLayer).getImage())
                painter.end()
            
            selection = selection.copy(bound.toAlignedRect())
            QGuiApplication.clipboard().setImage(selection)
        
        if CanvasOperation.DELETE in self.changes.operations or CanvasOperation.CUT in self.changes.operations:
            mask = self.mask.getImage()
            if not self.floating:
                painter = self.getLayer(self.activeLayer).beginPaint()
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                painter.drawImage(0,0,mask)
                self.getLayer(self.activeLayer).endPaint()
            else:
                self.getLayer(self.floatingLayer).changed = True
                self.renderMask()
                self.restoredSelection = self.changes.selection.copy()
                self.restoredSelection.applyOffset()
                self.restoredSelection.clearMask()
                self.resetMoving()
                self.floating = False

        if CanvasOperation.MOVE in self.changes.operations and not self.floating:
            selection = QImage(self.mask.getImage())

            painter = self.mask.beginPaint()
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.drawImage(0,0,self.getLayer(self.activeLayer).getImage())
            self.mask.endPaint()
            
            painter = self.getLayer(self.activeLayer).beginPaint()
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawImage(0,0,selection)
            self.getLayer(self.activeLayer).endPaint()
            
            self.resetMoving()
            self.floating = True
            self.floatingLayer = self.activeLayer
            self.getLayer(self.floatingLayer).changed = True

        if CanvasOperation.SET_MOVE in self.changes.operations:
            self.getLayer(self.floatingLayer).changed = True
            self.floatingPosition = self.floatingPosition + self.floatingOffset
            self.floatingOffset = QPointF(0,0)
        
        if CanvasOperation.UPDATE_MOVE in self.changes.operations:
            self.floatingOffset = self.changes.move

        if CanvasOperation.DESELECT in self.changes.operations:
            if self.floating:
                self.changes.operations.add(CanvasOperation.ANCHOR)

        if CanvasOperation.ANCHOR in self.changes.operations:
            if self.floating:
                self.checkpoints.append(self.makeCheckpoint())

                selection = QImage(self.mask.getImage())

                offset = alignQPointF(self.floatingPosition + self.floatingOffset)

                painter = self.getLayer(self.floatingLayer).beginPaint()
                painter.drawImage(offset, selection)
                self.getLayer(self.floatingLayer).endPaint()

                self.renderMask()
                self.resetMoving()

                self.changes.selection.clearMask()
                self.changes.selection.applyOffset()
                self.restoredSelection = self.changes.selection

                self.floating = False

        if CanvasOperation.DESELECT in self.changes.operations:
            self.changes.selection.clear()
            self.restoredSelection = self.changes.selection

        if CanvasOperation.FUZZY in self.changes.operations:
            source = self.getLayer(self.activeLayer).getImage()
            source = QImagetoCV2(source)
            source = np.ascontiguousarray(source[:,:,:3])
            origin = (int(self.changes.position.x()), int(self.changes.position.y()))

            threshold = (self.changes.select.threshold*2.56,)*3

            source = cv2.floodFill(source, None, origin, (255, 255, 255), threshold, threshold, 4|cv2.FLOODFILL_FIXED_RANGE)[2]
            source = source[1:-1,1:-1]*255
            source = np.dstack((source,)*4)
            source = CV2toQImage(source)
            source = self.convertMask(source)
            
            painter = self.mask.beginPaint()
            if self.changes.selection._mode in {CanvasSelectionMode.NORMAL}:
                gl.glClearColor(0,0,0,0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            elif self.changes.selection._mode in {CanvasSelectionMode.SUBTRACT}:
                painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            painter.drawImage(0,0,source)
            self.mask.endPaint()
            self.restoredSelection = self.changes.selection.copy()
            self.restoredSelection.setMask(self.mask.getImage())

        if save:
            self.checkpoints.append(self.makeCheckpoint())
            self.atCheckpoint = True
        else:
            self.atCheckpoint = False

    def convertMask(self, inMask):
        inMask = inMask.convertToFormat(QImage.Format_Alpha8)
        
        outMask = QImage(inMask.size(), QImage.Format_ARGB32_Premultiplied)
        outMask.fill(QColor.fromRgbF(1.0, 1.0, 1.0, 1.0))
        outMask.setAlphaChannel(inMask)

        return outMask

    def resetMoving(self):
        self.floatingOffset = QPointF(0,0)
        self.floatingPosition = QPointF(0,0)
        self.floatingLayer = -1

    def getFloatingThumbnail(self):
        mask = self.mask.getImage()
        image = QImage(self.size, QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter()
        painter.begin(image)
        painter.drawImage(self.floatingPosition + self.floatingOffset, mask)
        painter.end()
        return image.scaledToWidth(128, mode=Qt.SmoothTransformation)