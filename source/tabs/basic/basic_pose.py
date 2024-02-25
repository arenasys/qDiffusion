from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QSize, Qt, QRect, QRectF, QPointF
from PyQt5.QtGui import QImage, QColor, QPainter, QBrush, QPolygonF
import math

NAMES = [
    "Nose", "Neck", "Right Shoulder", "Right Elbow", "Right Wrist", "Left Shoulder", \
    "Left Elbow", "Left Wrist", "Right Hip", "Right Knee", "Right Ankle", "Left Hip", \
    "Left Knee", "Left Ankle", "Right Eye", "Left Eye", "Right Ear", "Left Ear"
]

LIMBS = [
    [2, 3], [2, 6], [3, 4], [4, 5], [6, 7], [7, 8], [2, 9], [9, 10], \
    [10, 11], [2, 12], [12, 13], [13, 14], [2, 1], [1, 15], [15, 17], \
    [1, 16], [16, 18], [3, 17], [6, 18]
]

COLORS = [
    [255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0], [85, 255, 0], [0, 255, 0], \
    [0, 255, 85], [0, 255, 170], [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [85, 0, 255], \
    [170, 0, 255], [255, 0, 255], [255, 0, 170], [255, 0, 85]
]

DEFAULT = [
    [0.5, 0.05], [0.5, 0.2], [0.2, 0.2], [0.1, 0.35], [0.0, 0.55], [0.8, 0.2], \
    [0.9, 0.35], [1.0, 0.55], [0.3, 0.55], [0.3, 0.78], [0.3, 1.0], [0.7, 0.55], \
    [0.7, 0.78], [0.7, 1.0], [0.4, 0.0], [0.6, 0.0], [0.3, 0.05], [0.7, 0.05]
]

class PoseNode(QObject):
    updated = pyqtSignal()
    def __init__(self, parent, point, index):
        super().__init__(parent)

        self._point = QPointF()
        if point:
            self._point = QPointF(point[0], point[1])

        self._offset = QPointF()

        self._origin = QPointF()
        self._scale = QPointF()
        self._rotation = 0

        self._index = index
    
    @pyqtProperty(QPointF, notify=updated)
    def point(self):
        if self._origin.isNull():
            return self.appliedOffset()
        elif not self._scale.isNull():
            return self.appliedScale()
        elif not self._rotation == 0:
            return self.appliedRotation()
        return self._point
        
    @point.setter
    def point(self, point):
        self._point = point
        self.updated.emit()

    @pyqtSlot(QPointF)
    def setOffset(self, offset):
        self._offset = offset
        self.updated.emit()

    @pyqtSlot()
    def applyOffset(self):
        if self._offset.isNull():
            return
        self._point = self.appliedOffset()
        self._offset = QPointF()
        self.updated.emit()

    def appliedOffset(self):
        return self._point + self._offset
    
    @pyqtSlot(QPointF, QPointF)
    def setScale(self, origin, scale):
        self._origin = origin
        self._scale = scale
        self._rotation = 0
        self.updated.emit()

    @pyqtSlot(QPointF, float)
    def setRotation(self, origin, rotation):
        self._origin = origin
        self._scale = QPointF()
        self._rotation = rotation
        self.updated.emit()

    @pyqtSlot()
    def applyTransform(self):
        if self._origin.isNull():
            return
        self._point = self.point
        self._origin = QPointF()
        self._scale = QPointF()
        self._rotation = 0
        self.updated.emit()

    def appliedScale(self):
        return QPointF(
            ((self._point.x() - self._origin.x()) * self._scale.x()) + self._origin.x(),
            ((self._point.y() - self._origin.y()) * self._scale.y()) + self._origin.y()
        )

    def appliedRotation(self):
        rc = math.cos(self._rotation)
        rs = math.sin(self._rotation)

        px, py = self._point.x(), self._point.y()
        ox, oy = self._origin.x(), self._origin.y()

        return QPointF(
            ((px-ox)*rc - (py-oy)*rs) + ox, 
            ((py-oy)*rc + (px-ox)*rs) + oy
        )

    @pyqtProperty(bool, notify=updated)
    def isNull(self):
        return self._point.isNull()
    
    @pyqtProperty(QColor, notify=updated)
    def color(self):
        color = COLORS[self._index]
        return QColor(color[0], color[1], color[2])
    
    @pyqtProperty(str, notify=updated)
    def name(self):
        return NAMES[self._index]
        
    @pyqtProperty(QRectF, notify=updated)
    def bound(self):
        return self.parent().bound
    
    @pyqtSlot()
    def delete(self):
        self.parent().deleteNode(self)

    @pyqtSlot(QPointF)
    def attach(self, position):
        self.parent().attachNode(self, position)

    @pyqtSlot(QRectF, bool)
    def flip(self, bound, vertical):
        pos = self._point - bound.topLeft()
        pos = QPointF(pos.x()/bound.width(), pos.y()/bound.height())
        if vertical:
            pos = QPointF(pos.x(), 1 - pos.y())
        else:
            pos = QPointF(1 - pos.x(), pos.y())
        pos = QPointF(pos.x()*bound.width(), pos.y()*bound.height())
        pos = pos + bound.topLeft()

        self._point = pos
        self.updated.emit()

class PoseEdge(QObject):
    updated = pyqtSignal()
    nullUpdated = pyqtSignal()
    def __init__(self, parent, nodeA, nodeB, index):
        super().__init__(parent)

        self._nodeA = nodeA
        self._nodeB = nodeB

        self._index = index

        self._null = self.nodeA.isNull or self.nodeB.isNull
        self._nodeA.updated.connect(self.nodeUpdated)
        self._nodeB.updated.connect(self.nodeUpdated)

    @pyqtProperty(PoseNode, notify=updated)
    def nodeA(self):
        return self._nodeA
    
    @pyqtProperty(PoseNode, notify=updated)
    def nodeB(self):
        return self._nodeB

    @pyqtProperty(bool, notify=nullUpdated)
    def isNull(self):
        return self._null
    
    @pyqtSlot()
    def nodeUpdated(self):
        null = self.nodeA.isNull or self.nodeB.isNull 
        if null != self._null:
            self._null = null
            self.nullUpdated.emit()
    
    @pyqtProperty(QColor, notify=updated)
    def color(self):
        color = COLORS[self._index]
        return QColor(color[0], color[1], color[2])
    
    @pyqtProperty(QRectF, notify=updated)
    def bound(self):
        return self.parent().bound

class Pose(QObject):
    boundUpdated = pyqtSignal()
    updated = pyqtSignal()
    def __init__(self, parent=None, points=[]):
        super().__init__(parent)
        self._nodes = [PoseNode(self, p, i) for i, p in enumerate(points)]
        self._edges = []
        for i in range(17):
            limb = [LIMBS[i][0]-1, LIMBS[i][1]-1]
            a = self._nodes[limb[0]]
            b = self._nodes[limb[1]]
            self._edges += [PoseEdge(self, a, b, i)]

    @pyqtProperty(list, notify=updated)
    def nodes(self):
        return self._nodes
    
    def encode(self):
        return [None if n.isNull else (n._point.x(), n._point.y()) for n in self._nodes]

    def isEmpty(self):
        return all([n.isNull for n in self._nodes])

    @pyqtSlot(PoseNode)
    def deleteNode(self, node):
        if not node in self._nodes:
            return
        
        node._point = QPointF()
        node.updated.emit()

    def findClosest(self, position):
        closest = None
        minimal = None
        for n in self._nodes:
            if n.isNull:
                continue

            dist = position - n._point
            dist = (dist.x()**2 + dist.y()**2)**0.5
            if not closest or dist < minimal:
                closest = n
                minimal = dist
        return closest

    def doAttach(self, node, closest, size):
        default = DEFAULT[node._index]
        origin = DEFAULT[closest._index]

        delta = QPointF((default[0]-origin[0])*size.x(), (default[1]-origin[1])*size.y())
        position = closest._point + delta

        node._point = position
        node.updated.emit()

    def guessBound(self, aspect=1):
        bound = self.bound
        bound_w, bound_h = bound.width(), bound.height()
        if bound_w == 0 or bound_h == 0:
            bound_w = 0.3/aspect
            bound_h = 0.7
        return QPointF(bound_w, bound_h)

    @pyqtSlot(PoseNode, QPointF)
    def attachNode(self, node, position):
        if not node in self._nodes:
            return
        
        closest = self.findClosest(position)
        bound = self.guessBound()

        self.doAttach(node, closest, bound)
    
    @pyqtSlot(float)
    def attachAll(self, aspect):
        bound = self.guessBound(aspect)

        while True:
            attached = False
            for source in self._nodes:
                if source.isNull:
                    continue
                repair = self.getRepairable(source)
                for node in repair:
                    self.doAttach(node, source, bound)
                    attached = True
            if not attached:
                break

    @pyqtProperty(list, notify=updated)
    def edges(self):
        return self._edges
    
    @pyqtSlot(PoseNode, result=list)
    def getRepairable(self, node):
        if not node in self._nodes:
            return []
        
        repairable = []
        idx = node._index
        for i in range(17):
            limb = [LIMBS[i][0]-1, LIMBS[i][1]-1]
            if idx in limb:
                other_idx = limb[0] if limb[1] == idx else limb[1]
                if self._nodes[other_idx].isNull:
                    repairable += [self._nodes[other_idx]]
        
        return repairable
    
    @pyqtSlot(result=int)
    def repairAmount(self):
        return len([n for n in self._nodes if n.isNull])

    @pyqtProperty(QRectF, notify=boundUpdated)
    def bound(self):
        poly = QPolygonF([n.point for n in self.nodes if not n.isNull])
        return poly.boundingRect()

    def drawPoses(poses, size, original, crop):
        w, h = int(size.width()), int(size.height())
        cx, cy = int(crop.left()), int(crop.top())
        cw, ch = int(crop.width()), int(crop.height())
        z = max(w,h)/100

        image = original.copy(cx, cy, cw, ch)
        image = image.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        painter = QPainter(image)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0,0,0,200)))
        painter.drawRect(QRect(0, 0, w, h))

        for pose in poses:
            for i in range(17):
                limb = [LIMBS[i][0]-1, LIMBS[i][1]-1]
                a = pose[limb[0]]
                b = pose[limb[1]]
                if a == None or b == None:
                    continue

                aX, aY = a[0]*w, a[1]*h
                bX, bY = b[0]*w, b[1]*h

                mX, mY = (aX + bX)/2, (aY + bY)/2

                length = ((aX - bX) ** 2 + (aY - bY) ** 2) ** 0.5
                angle = math.degrees(math.atan2(aY - bY, aX - bX))

                painter.save()
                painter.translate(mX, mY)
                painter.rotate(angle)
                painter.setBrush(QColor(*COLORS[i]))
                painter.drawEllipse(QPointF(0, 0), float(length/2), float(z))
                painter.restore()

        painter.setBrush(QBrush(QColor(0,0,0,102)))
        painter.drawRect(QRect(0, 0, w, h))
        
        for pose in poses:
            for i in range(18):
                point = pose[i]
                if not point:
                    continue

                x, y = point[0]*w, point[1]*h

                painter.setBrush(QColor(*COLORS[i]))
                painter.drawEllipse(QPointF(x, y), float(z), float(z))

        painter.end()
        return image
    
    def printPose(self):
        p = []
        for n in self._nodes:
            if(n.isNull):
                p += [None]
            else:
                p += [(n._point.x(), n._point.y())]
        print(p)

    def makeAtPosition(position, size):
        w, h = int(0.3 * size.x()), int(0.7 * size.y())
        x, y = position.x() - (w*0.5), position.y() - (h*0.2)

        nodes = []
        for d in DEFAULT:
            nodes += [[x + (d[0]*w), y + (d[1]*h)]]
        
        return nodes