import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"

Item {
    id: root
    property int itemWidth
    property int itemHeight

    property var scale: 1.0
    property var item: itm
    property var mouse: itmMouse
    property var ctrlZoom: false

    signal contextMenu()

    clip: true

    CenteredItem {
        id: itm
        anchors.centerIn: parent
        maxWidth: Math.min(root.width, root.itemWidth)
        maxHeight: Math.min(root.height, root.itemHeight)
        itemWidth: root.itemWidth
        itemHeight: root.itemHeight
        fill: true
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.MiddleButton

        property var startX: 0
        property var startY: 0
        property var posX: 0
        property var posY: 0
        property var dragging: false

        onPressed: {
            posX = itm.x
            posY = itm.y
            startX = mouseX
            startY = mouseY
            dragging = true
        }

        onReleased: {
            dragging = false
        }

        onPositionChanged: {
            if(dragging) {
                itm.anchors.centerIn = undefined

                itm.x = posX + (mouseX - startX)
                itm.y = posY + (mouseY - startY)

                bound()
            }
        }

        function bound() {
            var dx = (itm.maxWidth - itm.width)/2
            var dy = (itm.maxHeight - itm.height)/2

            var x = itm.x + dx
            var y = itm.y + dy
            var w = itm.width
            var h = itm.height

            if(x + w - dx < root.width/2)
                x = root.width/2 - w + dx
            if(y + h - dy < root.height/2)
                y = root.height/2 - h + dy

            if(x > root.width/2 + dx)
                x = root.width/2 + dx

            if(y > root.height/2 + dy)
                y = root.height/2 + dy

            itm.x = x - dx
            itm.y = y - dy
        }

        function scale(cx, cy, d) {
            itm.anchors.centerIn = undefined

            d = root.scale * d

            var f = ((root.scale + d)/root.scale) -1

            if(root.scale + d < 0.1) {
                return
            }

            if(root.scale + d > 10) {
                return
            }

            root.scale += d

            itm.maxWidth = root.scale * Math.min(root.width, root.itemWidth)
            itm.maxHeight = root.scale * Math.min(root.height, root.itemHeight)

            var dx = f*(cx - itm.x)
            var dy = f*(cy - itm.y)

            itm.x -= dx
            itm.y -= dy
            posX -= dx
            posY -= dy

            bound()
        }

        onWheel: {
            var ctrl = wheel.modifiers & Qt.ControlModifier
            if(!ctrl && root.ctrlZoom) {
                return
            }
            if(wheel.angleDelta.y < 0) {
                wheel.accepted = true
                scale(wheel.x, wheel.y, -0.1)
            } else {
                wheel.accepted = true
                scale(wheel.x, wheel.y, 0.1)
            }
        }
    }

    onItemHeightChanged: {
        reset()
    }

    onItemWidthChanged: {
        reset()
    }

    onWidthChanged: {
        reset()
    }

    onHeightChanged: {
        reset()
    }

    function reset() {
        root.scale = 1
        itm.anchors.centerIn = root
        itm.maxWidth = Math.min(root.width, root.itemWidth)
        itm.maxHeight = Math.min(root.height, root.itemHeight)
    }

    MouseArea {
        id: itmMouse
        anchors.fill: itm
        hoverEnabled: false

        acceptedButtons: Qt.LeftButton | Qt.RightButton

        drag.target: itm

        onClicked: {
            switch(mouse.button) {
            case Qt.RightButton:
                root.contextMenu()
                break;
            default:
                mouse.accepted = false
                break;
            }
        }
    }
}