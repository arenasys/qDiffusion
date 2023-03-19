import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    anchors.fill: parent
    property var editing: false
    visible: false

    property var target

    function open(target) {
        root.editing = target.role == 2 && !target.empty && target.linked
        root.target = target

        if(root.editing) {
            canvas.setupBasic(root.target.image, root.target.linkedImage)
            canvas.visible = true
            movable.itemWidth = root.target.linkedWidth
            movable.itemHeight = root.target.linkedHeight
        } else {
            canvas.visible = false
            bg.image = root.target.image
            movable.itemWidth = root.target.width
            movable.itemHeight = root.target.height
        }
        movable.reset()
        canvas.update()

        root.visible = true
        root.forceActiveFocus()
    }

    function close() {
        if(root.editing) {
            root.target.setImageData(canvas.getImage())
        }
        root.visible = false
    }

    Rectangle {
        anchors.fill: parent
        color: "#90000000"
    }

    MouseArea {
        anchors.fill: parent
    }

    MovableItem {
        id: movable
        anchors.fill: parent
        itemWidth: 0
        itemHeight: 0

        Item {
            id: item
            x: Math.floor(parent.item.x)
            y: Math.floor(parent.item.y)
            width: Math.ceil(parent.item.width)
            height: Math.ceil(parent.item.height)
        }

        SGlow {
            visible: movable.item.width > 0
            target: movable.item
        }

        TransparencyShader {
            anchors.fill: item
        }

        ImageDisplay {
            id: bg
            anchors.fill: item
        }

        AdvancedCanvas {
            id: canvas
            anchors.fill: item
            smooth: sourceSize.width*1.1 < width && sourceSize.height*1.1 < height ? false : true
            brush.color: "#ffffff"
        }

        Item {
            id: rings
            visible: root.editing && mousePosition != Qt.point(0,0)
            anchors.fill: item
            property var mousePosition: Qt.point(0,0)
            property var size: canvas.brush.size*(canvas.width/canvas.sourceSize.width)

            Rectangle {
                id: ringBlack
                radius: width/2
                width: parent.size
                height: width
                x: (parent.mousePosition.x*item.width)-width/2
                y: (parent.mousePosition.y*item.height)-height/2
                color: "transparent"
                border.width: 1
                border.color: "black"
            }
            Rectangle {
                id: ringWhite
                radius: width/2
                width: parent.size + 1
                height: width
                x: (parent.mousePosition.x*item.width)-width/2
                y: (parent.mousePosition.y*item.height)-height/2
                color: "transparent"
                border.width: 1
                border.color: "white"
            }
        }

        MouseArea {
            id: mouseArea
            visible: root.editing
            anchors.fill: parent
            hoverEnabled: true

            acceptedButtons: Qt.LeftButton | Qt.RightButton

            function getPosition(mouse) {
                return Qt.point(mouse.x, mouse.y)
            }

            onPressed: {
                if (mouse.button === Qt.LeftButton) {
                    canvas.brush.modeIndex = 0
                } else if (mouse.button === Qt.RightButton) {
                    canvas.brush.modeIndex = 1
                }
                canvas.mousePressed(getPosition(mouse), mouse.modifiers)
            }

            onReleased: {
                canvas.mouseReleased(getPosition(mouse), mouse.modifiers)
            }

            onPositionChanged: {
                rings.mousePosition = Qt.point((mouseX - item.x)/item.width, (mouseY - item.y)/item.height)

                if(mouse.buttons) {
                    canvas.mouseDragged(getPosition(mouse), mouse.modifiers)
                }
            }

            onWheel: {
                if (!(wheel.modifiers & Qt.ControlModifier)) {
                    wheel.accepted = false
                    return
                }
                var o = 5
                if(canvas.brush.size < 20) {
                    o = 1
                }
                if(wheel.angleDelta.y > 0) {
                    
                    canvas.brush.size = Math.min(canvas.brush.size+o, 500)
                } else {
                    canvas.brush.size = Math.max(canvas.brush.size-o, 1)
                }
            }
        }

        Timer {
            id: cooldown
            property var canvasCooldown: false
            interval: 17; running: true; repeat: true
            onTriggered: {
                if(canvas.needsUpdate && canvas.visible) {
                    canvas.update()
                } else {
                    cooldown.canvasCooldown = false
                }
            }
        }

        Timer {
            interval: 100; running: true; repeat: true
            onTriggered: {
                if(canvas.visible) {
                    canvas.update()
                }
            }
        }
    }

    Keys.onPressed: {
            event.accepted = true
            switch(event.key) {
            case Qt.Key_Escape:
                root.close()
                break;
            default:
                event.accepted = false
                break;
            }
        }
}