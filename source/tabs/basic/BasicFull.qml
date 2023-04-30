import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property var editing: false
    property var file: null
    property var image: null
    visible: false

    onImageChanged: {
        if(image) {
            bg.image = image
        }
    }

    signal contextMenu()

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
            root.file = null
            root.visible = false
            return
        }

        root.editing = (target.role == 2 || target.role == 3) && BASIC.openedArea == "input"

        var reset = false

        if(root.editing) {
            BASIC.setupCanvas(canvas.wrapper, root.target)
            root.syncSubprompt()
            canvas.visible = true
            root.image = root.target.linkedImage
            reset = movable.itemWidth != root.target.linkedWidth || movable.itemHeight != root.target.linkedHeight
            movable.itemWidth = root.target.linkedWidth
            movable.itemHeight = root.target.linkedHeight
            root.file = null
        } else {
            canvas.visible = false
            root.image = Qt.binding(function () { return root.target.image; })
            reset = movable.itemWidth != root.target.width || movable.itemHeight != root.target.height
            movable.itemWidth = root.target.width
            movable.itemHeight = root.target.height
            root.file = root.target.file
        }

        if(reset || !root.visible) {
            movable.reset()
        }
        canvas.update()

        root.visible = true
    }

    function sync() {
        if(root.editing) {
            BASIC.syncCanvas(canvas.wrapper, root.target)
        }
    }

    function syncSubprompt() {
        if(root.editing && root.target && root.target.role == 3) {
            BASIC.syncSubprompt(canvas.wrapper, subpromptColumn.selectedArea, root.target)
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
            root.image = root.image
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

        onContextMenu: {
            root.contextMenu()
        }

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
            onImageChanged: {
                movable.itemWidth = root.target.width
                movable.itemHeight = root.target.height
            }
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
            opacity: root.target && root.target.linked ? 0.8 : 1.0

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
                border.color: show ? (root.target.extentWarning ? "red" : "#00ff00") : "#00ff00"
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

    Rectangle {
        id: subpromptBar
        visible: root.target && root.target.role == 3 && BASIC.parameters.subprompts.length > 0
        width: 40
        height: subpromptColumn.height+7
        anchors.verticalCenter: movable.verticalCenter
        anchors.left: movable.left
        anchors.leftMargin: -2
        color: COMMON.bg2
        ListView {
            id: subpromptColumn
            model: BASIC.parameters.subprompts
            property var selectedArea: 0
            onModelChanged: {
                selectedArea = Math.max(0, Math.min(selectedArea, model.length-1))
            }
            height: contentHeight
            width: parent.width
            delegate: Item {
                height: width-7
                width: subpromptBar.width
                property var color: COMMON.accent(index/4)
                property var selected: subpromptColumn.selectedArea == index
                Rectangle {
                    id: colorRect
                    color: Qt.lighter(parent.color, selected ? 1.2 : 1)
                    anchors.fill: parent
                    anchors.topMargin: 7
                    anchors.leftMargin: 7
                    anchors.rightMargin: 7
                }
                Rectangle {
                    anchors.fill: colorRect
                    border.color: Qt.lighter(parent.color, 0.9 + (selected ? 0.5 : 0))
                    border.width: 3
                    color: "transparent"
                }
                Rectangle {
                    anchors.fill: colorRect
                    border.color: Qt.lighter(parent.color, 1.5 + (selected ? 0.5 : 0))
                    border.width: 2
                    color: "transparent"
                }
                Rectangle {
                    anchors.fill: colorRect
                    border.color: Qt.lighter(parent.color, 1.2 + (selected ? 0.5 : 0))
                    border.width: 1
                    color: "transparent"
                }

                Rectangle {
                    anchors.fill: colorRect
                    anchors.margins: 5
                    color: Qt.lighter(parent.color, selected ? 1.5 : 0.6)
                }

                MouseArea {
                    anchors.fill: colorRect
                    onPressed: {
                        subpromptColumn.selectedArea = index
                        root.syncSubprompt()
                    }
                }

            }
        }
        border.color: COMMON.bg4
        border.width: 2
    }

    Connections {
        target: BASIC.parameters
        function onSubpromptsChanged(subprompts) {
            root.syncSubprompt()
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_C:
                if(root.target != null && BASIC.openedArea == "output") {
                    root.target.copy()
                }
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
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
            case Qt.Key_Alt:
                movable.reset()
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }
}