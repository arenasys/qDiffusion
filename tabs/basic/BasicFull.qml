import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property var editing: false
    visible: false

    function getTarget(index, area) {
        if(index == -1) {
            return null
        }
        if(area == "input") {
            return BASIC.inputs[index]
        }
        if(area == "output") {
            return BASIC.outputs(index)
        }
    }

    Connections {
        target: BASIC
        function onOpenedUpdated() {
            if(root.target == null) {
                root.forceActiveFocus()
            }
            root.target = getTarget(BASIC.openedIndex, BASIC.openedArea)
        }
    }

    property var target: null
    property var changing: ""

    onTargetChanged: {
        if(target == null) {
            root.visible = false
            return
        }

        root.editing = target.role == 2 && !target.empty && target.linked

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
    }

    function sync() {
        if(root.editing) {
            root.target.setImageData(canvas.getImage())
        }
    }

    function change() {
        switch(root.changing) {
        case "left":
            BASIC.left();
            break;
        case "right":
            BASIC.right()
            break;
        case "close":
            BASIC.close()
            break;
        case "delete":
            BASIC.delete()
            break;
        }
        root.changing = ""
    }

    function close() {
        if(root.editing) {
            changing = "close"
            if(!canvas.forceSync()) {
                root.change()
            }
        } else {
            BASIC.close()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#b0000000"
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if(mouse.button == Qt.LeftButton) {
                root.close()
            }
        }
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
            smooth: implicitWidth*1.25 < width && implicitHeight*1.25 < height ? false : true
        }

        AdvancedCanvas {
            id: canvas
            anchors.fill: item
            smooth: sourceSize.width*1.1 < width && sourceSize.height*1.1 < height ? false : true
            brush.color: "#ffffff"
            brush.hardness: 99.9

            onChanged: {
                root.sync()
                root.change()
            }
        }

        Item {
            id: extent
            visible: root.editing
            anchors.fill: item

            Rectangle {
                property var factor: (canvas.width/canvas.sourceSize.width)
                border.color: "red"
                border.width: 1
                color: "transparent"
                property var show: root.target != null && root.target.extent != undefined

                x: show ? root.target.extent.x*factor : 0
                y: show ? root.target.extent.y*factor : 0
                width: show ? root.target.extent.width*factor : 0
                height: show ? root.target.extent.height*factor : 0
            }
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
            case Qt.Key_Left:
                if(root.editing) {
                    changing = "left"
                    if(!canvas.forceSync()) {
                        root.change()
                    }
                } else {
                    BASIC.left()
                }
                break;
            case Qt.Key_Right:
                if(root.editing) {
                    changing = "right"
                    if(!canvas.forceSync()) {
                        root.change()
                    }
                } else {
                    BASIC.right()
                }
                break;
            case Qt.Key_Escape:
                if(root.editing) {
                    changing = "close"
                    if(!canvas.forceSync()) {
                        root.change()
                    }
                } else {
                    BASIC.close()
                }
                break;
            case Qt.Key_Delete:
                if(root.editing) {
                    changing = "delete"
                    if(!canvas.forceSync()) {
                        root.change()
                    }
                } else {
                    BASIC.delete()
                }
                break;
            default:
                event.accepted = false
                break;
            }
        }
}