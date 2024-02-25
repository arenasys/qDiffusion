import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property var masking: false
    property var painting: false
    property var editing: masking || painting
    property var segmenting: false
    property var tiling: false
    property var posing: false
    property var file: null
    property var image: null
    visible: false

    property var color: painting ? colorPicker.color : "#ffffff"
    property var size: painting ? sizeSlider.value : rings.size
    property var hardness: painting ? hardnessSlider.value : 100
    property var spacing: painting ? spacingSlider.value : 10

    onImageChanged: {
        if(image) {
            bg.image = image
            bg.visible = true
        } else {
            bg.visible = false
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
    property var artifact: target != null && target.showingArtifact ? target.displayFull : null

    onArtifactChanged: {
        if(root.artifact != null) {
            artifact.image = root.artifact
            movable.itemWidth = root.target.width
            movable.itemHeight = root.target.height
        } else if(root.painting && root.target != null) {
            movable.itemWidth = root.target.originalWidth
            movable.itemHeight = root.target.originalHeight
        }
    }

    onTargetChanged: {
        if(target == null) {
            root.file = null
            root.visible = false
            return
        }

        if (BASIC.openedArea == "input" && (target.folder == undefined || target.folder == "")) {
            root.masking = target.isMask
            root.painting = !target.isMask && target.isCanvas && !target.isPose
            root.segmenting = (target.role == 5)
            root.tiling = target.isTile
            root.posing = target.isPose
        } else {
            root.masking = false
            root.painting = false
            root.segmenting = false
            root.tiling = false
            root.posing = false
        }

        var reset = false

        if(root.masking) {
            BASIC.setupCanvas(canvas.wrapper, root.target)
            root.syncSubprompt()
            canvas.visible = true
            root.image = root.target.linkedImage
            reset = movable.itemWidth != root.target.linkedWidth || movable.itemHeight != root.target.linkedHeight
            movable.itemWidth = root.target.linkedWidth
            movable.itemHeight = root.target.linkedHeight
            root.file = null
        } else if (root.painting) {
            BASIC.setupCanvas(canvas.wrapper, root.target)
            canvas.visible = true
            root.image = null
            movable.itemWidth = canvas.sourceSize.width
            movable.itemHeight = canvas.sourceSize.height
            root.file = null
        } else if (root.tiling) {
            canvas.visible = false
            root.image = Qt.binding(function () { return root.target.linked ? root.target.linkedImage : root.target.image; })
            reset = movable.itemWidth != (root.target.linked ? root.target.linkedWidth : root.target.width) || movable.itemHeight != (root.target.linked ? root.target.linkedHeight : root.target.height)
            movable.itemWidth = Qt.binding(function () { return root.target.linked ? root.target.linkedWidth : root.target.width; })
            movable.itemHeight = Qt.binding(function () { return root.target.linked ? root.target.linkedHeight : root.target.height; })
            root.file = null
        } else if (root.posing) {
            canvas.visible = false
            root.image = Qt.binding(function () { return root.target.originalCrop; })
            reset = movable.itemWidth != root.target.width || movable.itemHeight != root.target.height
            movable.itemWidth = root.target.width
            movable.itemHeight = root.target.height
            root.file = root.target.file
        } else {
            canvas.visible = false
            root.image = Qt.binding(function () { return root.target.displayFull; })
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
        root.image = root.image
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

        Item {
            id: points
            anchors.fill: item
            visible: root.segmenting && root.target
            property var label: [] 
            property var factor: item.width/bg.sourceWidth

            onFactorChanged: {
                pointDrag.point = null
            }

            MouseArea {
                id: pointDrag
                property var point: null
                anchors.fill: parent
                anchors.margins: 0
                property var startMouse: null
                property var startPoint: null
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onReleased: {
                    pointDrag.point = null
                    target.syncSegmentationPoints()
                }

                onDoubleClicked: {
                    var x = Math.floor(mouseX/points.factor)
                    var y = Math.floor(mouseY/points.factor)
                    if(mouse.button & Qt.LeftButton) {
                        var label = 1;
                        if(points.label.length > 0) {
                            label = points.label[0]
                        }
                        target.addSegmentationPoint(x, y, label)
                    } else {
                        target.addSegmentationPoint(x, y, 0)
                    }
                }

                onPointChanged: {
                    if(point != null) {
                        startMouse = Qt.point(mouseX, mouseY)
                        startPoint = Qt.point(point.pointX, point.pointY)
                    }
                }

                onPositionChanged: {
                    if(point != null) {
                        var deltaX = (mouseX - startMouse.x)/points.factor
                        var deltaY = (mouseY - startMouse.y)/points.factor

                        point.pointX = Math.max(Math.min(Math.round(startPoint.x + deltaX), bg.sourceWidth), 0)
                        point.pointY = Math.max(Math.min(Math.round(startPoint.y + deltaY), bg.sourceHeight), 0)
                    }
                }
            }

            Repeater {
                model: root.segmenting && root.target != null ? root.target.segmentationPoints : []

                delegate: Rectangle {
                    id: point
                    border.color: ["red", "#00ff00", "#0000ff", "#ffff00", "#00ffff", "#ff00ff","#ff8000", "#00ff80", "#8000ff", "#0080ff"][modelData.z]
                    border.width: 2
                    color: "transparent"

                    property var oldX: modelData.x
                    property var oldY: modelData.y

                    property var pointX: modelData.x
                    property var pointY: modelData.y

                    function sync() {
                        if(pointX != oldX || pointY != oldY) {
                            target.moveSegmentationPoint(oldX, oldY, pointX, pointY)
                            oldX = pointX
                            oldY = pointY
                        }
                    }

                    onPointXChanged: {
                        sync()
                    }

                    onPointYChanged: {
                        sync()
                    }

                    x: (pointX+0.5)*parent.factor - 3
                    y: (pointY+0.5)*parent.factor - 3

                    width: 6
                    height: 6

                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -3
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onPressed: {
                            if(mouse.buttons & Qt.LeftButton) {
                                pointDrag.point = point
                                mouse.accepted = false
                            } else {
                                target.deleteSegmentationPoint(oldX, oldY)
                            }
                        }
                    }
                }
            }
        }

        AdvancedCanvas {
            id: canvas
            anchors.fill: item
            smooth: sourceSize.width*1.1 < width && sourceSize.height*1.1 < height ? false : true

            brush.color: root.color
            brush.size: root.size
            brush.hardness: root.hardness
            brush.spacing: root.spacing

            opacity: root.target && root.masking && root.target.linked ? 0.8 : 1.0

            onChanged: {
                root.sync()
                root.change()
            }

            onColorSampled: function (color) {
                if(root.painting) {
                    colorPicker.setColor(color)
                }
            }
        }

        ImageDisplay {
            id: artifact
            visible: root.artifact != null && root.painting
            anchors.fill: item
            smooth: implicitWidth*1.25 < width && implicitHeight*1.25 < height ? false : true
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
            visible: root.tiling
            anchors.fill: item

            Repeater {
                id: tiles
                property var show: root.target != null && root.target.tiles != undefined
                model: show ? root.target.tiles : []

                Rectangle {
                    property var factor: (item.width/root.target.width)
                    border.color: Qt.hsva(index/tiles.model.length, 1.0, 1.0, 0.75)
                    border.width: 2
                    color: Qt.hsva(index/tiles.model.length, 1.0, 1.0, 0.1)

                    x: show ? modelData.x*factor : 0
                    y: show ? modelData.y*factor : 0
                    width: show ? Math.floor(modelData.width*factor) : 0
                    height: show ? Math.floor(modelData.height*factor) : 0
                }
            }
        }

        PoseEditor {
            id: poseEditor
            visible: root.posing
            anchors.fill: parent

            area.x: item.x
            area.y: item.y
            area.width: item.width
            area.height: item.height

            target: root.target != null && root.posing ? root.target : null
            poses: root.target != null && root.posing ? root.target.poses : []

            function addPose(position, aspect) {
                root.target.addPose(position, aspect)
            }

            function cleanPoses() {
                root.target.cleanPoses()
            }

            function undo() {
                root.target.undoPose()
            }

            function redo() {
                root.target.redoPose()
            }

            function clearRedo() {
                root.target.clearRedoPose()
            }

            function draw() {
                root.target.drawPose()
            }

            function close() {
                root.close()
            }
        }

        Item {
            id: rings
            visible: root.editing && !root.artifact && mousePosition != Qt.point(0,0)
            anchors.fill: item
            property var mousePosition: Qt.point(0,0)
            property var currentPosition: mouseArea.resizingBrush ? mouseArea.resizeStart : mousePosition
            
            property var size: 100
            property var displaySize: (mouseArea.resizingBrush ? mouseArea.getBrushRadius()*2 : root.size)*(canvas.width/canvas.sourceSize.width)

            Rectangle {
                id: ringBlack
                radius: width/2
                width: parent.displaySize
                height: width
                x: (parent.currentPosition.x*item.width)-width/2
                y: (parent.currentPosition.y*item.height)-height/2
                color: "transparent"
                border.width: 1
                border.color: "black"
            }
            Rectangle {
                id: ringWhite
                radius: width/2
                width: parent.displaySize + 1
                height: width
                x: (parent.currentPosition.x*item.width)-width/2
                y: (parent.currentPosition.y*item.height)-height/2
                color: "transparent"
                border.width: 1
                border.color: "white"
            }
        }

        MouseArea {
            id: mouseArea
            visible: root.editing && !root.artifact
            anchors.fill: parent
            hoverEnabled: true

            property var resizingBrush: false
            property var resizeStart

            acceptedButtons: Qt.LeftButton | Qt.RightButton

            function getPosition(mouse) {
                return Qt.point(mouse.x, mouse.y)
            }

            function getBrushRadius() {
                var distX = (resizeStart.x-rings.mousePosition.x)*canvas.sourceSize.width;
                var distY = (resizeStart.y-rings.mousePosition.y)*canvas.sourceSize.height;
                return Math.sqrt(distX*distX + distY * distY)
            }

            onPressed: {
                if(resizingBrush) {
                    return
                }
                if (mouse.button === Qt.LeftButton) {
                    canvas.brush.modeIndex = 0
                } else if (mouse.button === Qt.RightButton) {
                    canvas.brush.modeIndex = 1
                }
                
                canvas.mousePressed(getPosition(mouse), mouse.modifiers)
            }

            onReleased: {
                if(resizingBrush) {
                    return
                }
                if (!(mouse.modifiers & Qt.ControlModifier)) {
                    canvas.mouseReleased(getPosition(mouse), mouse.modifiers)
                }
            }

            onPositionChanged: {
                rings.mousePosition = Qt.point((mouseX - item.x)/item.width, (mouseY - item.y)/item.height)
                if(resizingBrush) {
                    return
                }

                if(mouse.buttons && !(mouse.modifiers & Qt.ControlModifier)) {
                    canvas.mouseDragged(getPosition(mouse), mouse.modifiers)
                }
            }

            onExited: {
                //rings.mousePosition = Qt.point(0,0)
            }

            onWheel: {
                if (!(wheel.modifiers & Qt.ControlModifier)) {
                    wheel.accepted = false
                    return
                }
                var o = wheel.angleDelta.y / 120
                if(root.size >= 20) {
                    o *= 5
                }
                o = Math.max(Math.min(canvas.brush.size+o, 500), 1)
                if(root.painting) {
                    sizeSlider.value = o
                } else {
                    rings.size = o
                }
            }

            onResizingBrushChanged: {
                if(resizingBrush) {
                    resizeStart = Qt.point(rings.mousePosition.x, rings.mousePosition.y)
                } else {
                    var o = Math.max(Math.min(getBrushRadius()*2, 500), 1)
                    if(root.painting) {
                        sizeSlider.value = o
                    } else {
                        rings.size = o
                    }
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

    Rectangle {
        id: paintBg
        visible: paintColumn.visible
        anchors.fill: paintColumn
        anchors.margins: -3
        anchors.bottomMargin: -5
        color: COMMON.bg0
        border.color: COMMON.bg4
        border.width: 3
    }

    Column {
        id: paintColumn
        width: 150
        visible: root.painting && !root.artifact
        anchors.verticalCenter: movable.verticalCenter
        anchors.left: movable.left

        OColumn {
            id: colorColumn
            text: "Color Picker"
            width: parent.width

            property var advanced: false

            ColorPicker {
                id: colorPicker
                width: parent.width
                height: width

                SIconButton {
                    anchors.bottom: colorPicker.bottom
                    anchors.right: colorPicker.right
                    anchors.bottomMargin: 28
                    anchors.rightMargin: 28
                    color: "transparent"
                    width: 18
                    height: 18
                    inset: 2
                    icon: "qrc:/icons/settings.svg"
                    iconColor: colorColumn.advanced ? COMMON.bg4 : COMMON.bg6
                    iconHoverColor: colorColumn.advanced ? COMMON.fg3 : COMMON.fg0

                    tooltip: colorColumn.advanced ? "Hide options" : "Show options"

                    onPressed: {
                        colorColumn.advanced = !colorColumn.advanced
                    }
                }

                Component.onCompleted: {
                    trueColor.r = Qt.binding(function() { return redSlider.value })
                    trueColor.g = Qt.binding(function() { return greenSlider.value })
                    trueColor.b = Qt.binding(function() { return blueSlider.value })
                    trueAlpha =  Qt.binding(function() { return alphaSlider.value })

                    trueColor.hsvHue = Qt.binding(function() { return hueSlider.value })
                    trueColor.hsvSaturation = Qt.binding(function() { return saturationSlider.value })
                    trueColor.hsvValue = Qt.binding(function() { return valueSlider.value })

                    trueHex = Qt.binding(function() { return hexInput.value })
                }
                
                onTrueColorChanged: {
                    redSlider.value = trueColor.r
                    greenSlider.value = trueColor.g
                    blueSlider.value = trueColor.b

                    hueSlider.value = trueColor.hsvHue
                    saturationSlider.value = trueColor.hsvSaturation
                    valueSlider.value = trueColor.hsvValue
                }

                onTrueAlphaChanged: {
                    alphaSlider.value = trueAlpha
                }

                onTrueHexChanged: {
                    hexInput.value = trueHex
                }
            }

            Rectangle {
                visible: colorColumn.advanced
                width: parent.width + 14
                x: -7
                height: 2
                color: COMMON.bg5
            }

            Column {
                visible: colorColumn.advanced
                width: parent.width

                OSlider {
                    id: redSlider
                    label: "R"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.r

                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: greenSlider
                    label: "G"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.g
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: blueSlider
                    label: "B"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.b
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: hueSlider
                    label: "H"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.hsvHue
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: saturationSlider
                    label: "S"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.hsvSaturation
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: valueSlider
                    label: "V"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.hsvValue
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OSlider {
                    id: alphaSlider
                    label: "A"
                    width: parent.width
                    height: 20

                    value: colorPicker.color.a
                    minValue: 0
                    maxValue: 1
                    precValue: 2
                    incValue: 0.01
                }

                OTextInput {
                    id: hexInput
                    width: parent.width
                    height: 20
                    label: "Hex"

                    value: colorPicker.trueHex
                    defaultValue: "#ffffff"
                    validator: RegExpValidator { regExp: /(#[0-9A-Fa-f]{8})|(#[0-9A-Fa-f]{6})/ }
                }
            }
        }

        OColumn {
            id: brushColumn
            width: parent.width
            hasDivider: false
            text: "Brush Settings"

            OSlider {
                id: sizeSlider
                label: "Size"
                width: parent.width
                height: 30

                value: 100
                minValue: 1
                maxValue: 500
                precValue: 0
                incValue: 1
            }

            OSlider {
                id: hardnessSlider
                label: "Hardness"
                width: parent.width
                height: 30

                value: 100
                minValue: 1
                maxValue: 100
                precValue: 0
                incValue: 1
            }

            OSlider {
                id: spacingSlider
                label: "Spacing"
                width: parent.width
                height: 30

                value: 10
                minValue: 1
                maxValue: 50
                precValue: 0
                incValue: 1
            }
        }
    }

    Keys.forwardTo: root.posing ? [poseEditor] : []
    
    Keys.onPressed: {
        if(root.posing) {
            event.accepted = false
            return
        }
        
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_C:
                if(root.target != null && BASIC.openedArea == "output") {
                    root.target.copy()
                }
                break;
            case Qt.Key_Z:
                if(root.target != null && root.segmenting) {
                    root.target.resetSegmentation()
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
            case Qt.Key_Up:
                root.target.prevDisplay()
                break;
            case Qt.Key_Down:
                root.target.nextDisplay()
                break;
            case Qt.Key_Escape:
                root.close()
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
                mouseArea.resizingBrush = true
                break;
            default:
                event.accepted = false
                break;
            }
            if(event.key >= Qt.Key_0 && event.key <= Qt.Key_9) {
                points.label.unshift(event.key - Qt.Key_0)
                event.accepted = true
            }
        }
    }

    Keys.onReleased: {
        switch(event.key) {
        case Qt.Key_Alt:
            mouseArea.resizingBrush = false
            break;
        default:
            break;
        }
        if(event.key >= Qt.Key_0 && event.key <= Qt.Key_9) {
            var index = points.label.indexOf(event.key - Qt.Key_0)
            if (index > -1) {
                points.label.splice(index, 1)
            }
        }

    }
}