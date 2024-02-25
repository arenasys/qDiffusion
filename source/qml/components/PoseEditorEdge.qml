import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    property var edge
    visible: !edge.isNull

    property var scale
    property var a: visible ? Qt.point(edge.nodeA.point.x*scale.x, edge.nodeA.point.y*scale.y) : Qt.point(0,0)
    property var b: visible ? Qt.point(edge.nodeB.point.x*scale.x, edge.nodeB.point.y*scale.y) : Qt.point(0,0)
    property var mid: visible ? Qt.point((a.x + b.x)/2, (a.y + b.y)/2) : Qt.point(0,0)
    property var length: visible ? Math.pow(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2), 0.5) : 0
    property var angle: visible ? Math.atan2(a.y - b.y, a.x - b.x) : 0

    x: mid.x - width/2
    y: mid.y - height/2
    width: Math.max(length, 8)
    height: Math.max(length, 8)

    Canvas {
        id: canvas
        visible: parent.visible
        renderStrategy: Canvas.Cooperative
        anchors.fill: parent
        contextType: "2d"

        onPaint: {
            var context = getContext("2d")
            context.reset()
            context.fillStyle = edge.color
            context.translate(width/2, height/2)
            context.rotate(angle)
            context.ellipse(-length/2, -8/2, length, 8)
            context.fill()
        }
    }
}