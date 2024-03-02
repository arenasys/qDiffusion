import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1

import gui 1.0

import "../style"

Item {
    id: root
    property var target
    property var poses
    property var relative: target != null ? target.relativePosing : false

    onRelativeChanged: {
        root.doClear(true)
    }

    property alias area: shownArea

    property var selected: []
    property var hovered: null
    property var pressed: mouseArea.start != null && selected.length != 0

    property var selectionArea: null
    property var boundArea: null

    function close() {

    }

    function tr(str, file = "PoseEditor.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    function syncSelection() {
        root.selected = root.selected.filter(function(item, pos) {
            return !item.isNull && root.selected.indexOf(item) == pos
        })
        syncBound()
    }

    function syncBound() {
        if(root.selected.length < 2) {
            root.boundArea = null
            return
        }

        var p = root.selected[0].point;

        var tl = Qt.point(p.x, p.y);
        var br = Qt.point(p.x, p.y);

        for(var i = 0; i < root.selected.length; i++) {
            p = root.selected[i].point;

            tl.x = Math.min(tl.x, p.x);
            tl.y = Math.min(tl.y, p.y);
            br.x = Math.max(br.x, p.x);
            br.y = Math.max(br.y, p.y);
        }

        root.boundArea = Qt.rect(tl.x, tl.y, br.x-tl.x, br.y-tl.y)
        return
    }

    function pointsToRect(a, b) {
        var tl = Qt.point(Math.min(a.x,b.x), Math.min(a.y,b.y))
        var br = Qt.point(Math.max(a.x,b.x), Math.max(a.y,b.y))
        return Qt.rect(tl.x, tl.y, br.x-tl.x, br.y-tl.y)
    }
    
    function doClear(selection) {
        mouseArea.clear()

        for(var i = 0; i < root.selected.length; i++) {
            root.selected[i].clearOffsets()
        }

        if(selection) {
            root.selected = []
        }
        root.selectionArea = null
        syncBound()
    }

    function doDraw() {
        root.target.clearRedoPose()
        root.target.drawPose()
    }

    function doDelete() {
        for(var i = 0; i < root.selected.length; i++) {
            root.selected[i].delete()
        }
        syncSelection()
        root.target.cleanPoses()
    }

    function doSelectAll() {
        if(root.relative) {
            return
        }

        var selection = []

        for(var i = 0; i < poses.length; i++) {
            for(var j = 0; j < poses[i].nodes.length; j++) {
                var node = poses[i].nodes[j];
                if(node.isNull) {
                    continue
                }
                selection.push(node)
            }
        }

        root.selected = selection
        root.syncSelection()
    }

    function getPose(node) {
        for(var i = 0; i < poses.length; i++) {
            for(var j = 0; j < poses[i].nodes.length; j++) {
                if(node == poses[i].nodes[j]) {
                    return poses[i]
                }
            }
        }
    }

    function doRepair() {
        if(root.selected.length == 0) {
            return
        }

        for(var i = 0; i < root.selected.length; i++) {
            var pose = getPose(root.selected[i])
            var repairNode = pose.getRepairable(root.selected[i])
            var repairPose = pose.repairAmount()

            if(repairNode.length != 0) {
                repairNode[0].attach(root.selected[i].point)
            } else if (repairPose != 0) {
                pose.attachAll(area.width/area.height)
            }
        }

        root.doDraw()
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        property var moveStart
        property var selectStart

        property var scaleOffset
        property var scaleOrigin
        property var scaleStart

        property var rotateOrigin
        property var rotateStart

        Timer {
            id: delay
            interval: 10
        }

        Timer {
            id: doubleClick
            interval: 200
        }

        function isContainedBy(obj) {
            var rect = obj.mapToItem(mouseArea, Qt.rect(0,0,obj.width,obj.height))
            return (mouseX >= rect.x && mouseX < rect.x + rect.width && mouseY >= rect.y && mouseY < rect.y + rect.height)
        }

        function getPosition() {
            return Qt.point((mouseX - (area.x + shownArea.x))*(area.size.x/area.width), (mouseY - (area.y + shownArea.y))*(area.size.y/area.height))
        }

        onPressed: {
            if(mouse.button == Qt.LeftButton) {
                if(scaleStart || rotateStart) {
                    return
                }

                var ctrl = mouse.modifiers & Qt.ControlModifier 

                var find = findNode()
                var node = find[0]

                if(root.relative) {
                    if(node != null) {
                        if(!root.selected.includes(node)) {
                            root.selected = [node]
                        }
                        moveStart = getPosition()
                    } else {
                        root.selected = []
                    }
                    return
                }

                if(root.boundArea != null && isContainedBy(boundBox)) {
                    if((ctrl && node == null) || !ctrl) {
                        moveStart = getPosition()
                        return
                    }
                }

                if(node == null) {
                    if(!ctrl) {
                        root.selected = []
                        syncSelection()
                    }
                    selectStart = getPosition()
                    return
                }

                var pose = find[1]
                var poseNodes = []
                for(var i = 0; i < pose.nodes.length; i++) {
                    if(pose.nodes[i].isNull) {
                        continue
                    }
                    poseNodes.push(pose.nodes[i])
                }

                if(doubleClick.running) {
                    if(mouse.modifiers & Qt.ControlModifier) {
                        if(root.selected.includes(node)) {
                            root.selected = root.selected.concat(poseNodes)
                        } else {
                            root.selected = root.selected.filter(function(item) {
                                return !poseNodes.includes(item)
                            })
                        }
                    }
                } else {
                    if(mouse.modifiers & Qt.ControlModifier) {
                        if(root.selected.includes(node)) {
                            root.selected = root.selected.filter(function(item) {
                                return item !== node
                            })
                        } else {
                            root.selected = root.selected.concat([node])
                        }
                    } else {
                        if(!root.selected.includes(node)) {
                            root.selected = [node]
                        }
                        moveStart = getPosition()
                    }
                }
                syncSelection()
                doubleClick.restart()
            } else if (mouse.button == Qt.RightButton) {
                var find = findNode()
                var node = find[0]
                var pose = find[1]
                var blank = false

                if(node == null) {
                    if(root.boundArea == null || !isContainedBy(boundBox)) {
                        blank = true
                    }
                } else if (!root.selected.includes(node)) {
                    root.selected = [node]
                    syncBound()
                }

                contextMenu.position = getPosition()
                contextMenu.node = node
                contextMenu.pose = pose
                contextMenu.blank = blank
                contextMenu.open()
            }
        }

        onReleased: {
            if(mouse.button == Qt.LeftButton) {
                var draw = false

                if(moveStart != null) {
                    if(root.relative) {
                        root.selected[0].applyRelativeOffset()
                    } else {
                        for(var i = 0; i < root.selected.length; i++) {
                            root.selected[i].applyOffset()
                        }
                    }
                    moveStart = null
                    draw = true
                }

                if(scaleStart != null || rotateStart != null) {
                    for(var i = 0; i < root.selected.length; i++) {
                        root.selected[i].applyTransform()
                    }

                    scaleStart = null
                    scaleOrigin = null
                    scaleOffset = null

                    rotateStart = null
                    rotateOrigin = null

                    draw = true
                    syncBound()
                }

                selectStart = null
                root.selectionArea = null

                if(draw) {
                    root.doDraw()
                }
            } else if (mouse.button == Qt.RightButton) {

            }
        }

        onPositionChanged: {
            var ctrl = mouse.modifiers & Qt.ControlModifier
            var shift = mouse.modifiers & Qt.ShiftModifier 

            if(moveStart) {
                if(root.relative) {
                    var end = getPosition()
                    var offset = Qt.point(end.x - moveStart.x, end.y - moveStart.y)

                    var allowAngle = ctrl || shift ? ctrl : true
                    var allowLength = ctrl || shift ? shift : false

                    root.selected[0].setRelativeOffset(offset, allowAngle, allowLength)
                } else {
                    var end = getPosition()
                    var offset = Qt.point(end.x - moveStart.x, end.y - moveStart.y)
                    for(var i = 0; i < root.selected.length; i++) {
                        root.selected[i].setOffset(offset)
                    }
                    syncBound()
                }
                return
            }

            if(selectStart) {
                var r = pointsToRect(selectStart, getPosition())
                root.selectionArea = r

                var selection = []
                for(var i = 0; i < poses.length; i++) {
                    for(var j = 0; j < poses[i].nodes.length; j++) {
                        var node = poses[i].nodes[j];
                        if(node.isNull) {
                            continue
                        }
                        var p = node.point
                        if(p.x >= r.x && p.x < r.x+r.width && p.y >= r.y && p.y < r.y+r.height) {
                            selection.push(node)
                        }
                    }
                }

                root.selected = selection
                syncBound()
                return
            }

            if(scaleStart) {
                var original = pointsToRect(scaleOrigin, scaleStart)

                var offsetted = Qt.point((mouseX - scaleOffset.x - (area.x + shownArea.x))/area.scale.x, (mouseY - scaleOffset.y - (area.y + shownArea.y))/area.scale.y)
                var current = pointsToRect(scaleOrigin, offsetted)
                var scale = Qt.point(current.width/original.width, current.height/original.height)

                if(ctrl) {
                    var a = Qt.point(current.width, current.height)
                    var b = Qt.point(original.width, original.height)

                    var f = (a.x*b.x + a.y*b.y)/(b.x*b.x + b.y*b.y)
                    var projection = Qt.point(f*b.x, f*b.y)

                    scale = Qt.point(projection.x/original.width, projection.y/original.height)
                }

                for(var i = 0; i < root.selected.length; i++) {
                    root.selected[i].setScale(scaleOrigin, scale)
                }

                syncBound()
                return
            }

            if(rotateStart) {
                var pos = getPosition()
                var current = Math.atan2(pos.x - rotateOrigin.x, pos.y - rotateOrigin.y)
                var delta = rotateStart - current

                if(ctrl) {
                    delta = Math.round(delta * (4/Math.PI))*(Math.PI/4)
                }

                for(var i = 0; i < root.selected.length; i++) {
                    root.selected[i].setRotation(rotateOrigin, delta)
                }

                syncBound()
                return
            }

            if(delay.running) {
                return
            }

            root.hovered = findNode()[0]
            delay.start()
        }

        onWheel: {
            if(relative && wheel.modifiers & Qt.ControlModifier) {
                var find = findNode()
                var node = find[0]
                var pose = find[1]

                if(!node) {
                    return
                }

                var s = 9
                if(wheel.modifiers & Qt.ShiftModifier) {
                    s = 36
                }

                var d = wheel.angleDelta.y / 120
                var o = -d * (Math.PI/s)
                pose.addRelativeAngle(node, o)
                root.doDraw()

            } else {
                wheel.accepted = false
            }
        }

        function findNode() {
            var position = getPosition()
            var offsetX = 8/area.scale.x
            var offsetY = 8/area.scale.x

            var closest = null
            var closestPose = null
            var distance = 0

            for(var i = 0; i < poses.length; i++) {
                for(var j = 0; j < poses[i].nodes.length; j++) {
                    var point = poses[i].nodes[j].point

                    var distX = Math.abs(position.x - point.x)
                    var distY = Math.abs(position.y - point.y)

                    if(distX > offsetX || distY > offsetY) {
                        continue
                    }

                    var dist = Math.pow(distX*distX + distY*distY, 0.5)

                    if(dist < distance || closest == null) {
                        closest = poses[i].nodes[j]
                        closestPose = poses[i]
                        distance = dist
                    }
                }
            }

            return [closest, closestPose]
        }

        function active() {
            return moveStart != null || selectStart != null || scaleStart != null || rotateStart != null
        }

        function clear() {
            mouseArea.moveStart = null
            mouseArea.selectStart = null
            mouseArea.scaleOffset = null
            mouseArea.scaleOrigin = null
            mouseArea.scaleStart = null
            mouseArea.rotateOrigin = null
            mouseArea.rotateStart = null
        }
    }

    Rectangle {
        id: bg
        x: shownArea.x
        y: shownArea.y
        width: shownArea.width
        height: shownArea.height
        color: "black"
        opacity: 0.8
    }

    Item {
        anchors.fill: parent
        Item {
            x: shownArea.x + area.x
            y: shownArea.y + area.y
            width: area.width
            height: area.height
            Repeater {
                model: poses
                Item {
                    id: entry
                    anchors.fill: parent
                    property var pose: modelData
                    property var nodes: pose.nodes
                    
                    Repeater {
                        model: pose.edges
                        PoseEditorEdge {
                            scale: area.scale
                            edge: modelData
                        }
                    }
                }
            }
        }
        Rectangle {
            x: 0
            y: 0
            width: parent.width
            height: bg.y
            color: "black"
            opacity: 0.8
        }
        Rectangle {
            x: 0
            y: bg.y+bg.height
            width: parent.width
            height: parent.height-y
            color: "black"
            opacity: 0.8
        }
        Rectangle {
            x: 0
            y: bg.y
            width: bg.x
            height: bg.height
            color: "black"
            opacity: 0.8
        }
        Rectangle {
            x: bg.x+bg.width
            y: bg.y
            width: parent.width-x
            height: bg.height
            color: "black"
            opacity: 0.8
        }

        layer.enabled: true
        opacity: 0.6
    }

    Item {
        id: shownArea

        Item {
            id: area
            property var size: root.target != null ? root.target.poseSize : Qt.point(shownArea.width, shownArea.height)
            property var crop: root.target != null ? root.target.poseCrop : Qt.rect(0,0,shownArea.width, shownArea.height)
            property var factor: Qt.point(shownArea.width/crop.width, shownArea.height/crop.height)
            property var scale: Qt.point(area.width/area.size.x, area.height/area.size.y)

            x: -crop.x * factor.x
            y: -crop.y * factor.y
            width: size.x * factor.x
            height: size.y * factor.y

            Item {
                anchors.fill: parent
                Repeater {
                    model: poses
                    Item {
                        id: entry
                        anchors.fill: parent
                        property var pose: modelData

                        Repeater {
                            model: pose.nodes
                            PoseEditorNode {
                                node: modelData
                                scale: area.scale
                                selected: root.selected.includes(node)
                                hovered: node == root.hovered
                            }
                        }
                    }
                }
            }

            Item {
                id: bound
                property var rect: root.boundArea
                visible: rect != null
                x: rect != null ? Math.floor(rect.x * area.scale.x) : 0
                y: rect != null ? Math.floor(rect.y * area.scale.y) : 0
                width: rect != null ? Math.floor(rect.width * area.scale.x) : 0
                height: rect != null ? Math.floor(rect.height * area.scale.y) : 0
            }

            Item {
                id: boundBox
                visible: bound.visible
                anchors.fill: bound
                anchors.margins: -12

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -1
                    color: "transparent"
                    border.color: "white"
                    border.width: 1
                    opacity: 0.3
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -2
                    color: "transparent"
                    border.color: "black"
                    border.width: 1
                    opacity: 0.3
                }

                Repeater {
                    model: [Qt.point(-1,-1), Qt.point(1,-1), Qt.point(1,1), Qt.point(-1,1)]
                    Item {
                        id: node
                        property var position: modelData
                        property var rotation: [Qt.point(0,1), Qt.point(-1,0), Qt.point(0,-1), Qt.point(1,0)][index]
                        anchors.horizontalCenter: position.x == -1 ? parent.left : parent.right
                        anchors.verticalCenter: position.y == -1 ? parent.top : parent.bottom
                        width: 8
                        height: 8

                        Item {
                            id: rotationNode

                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.horizontalCenterOffset: parent.rotation.x * 16
                            anchors.verticalCenterOffset: parent.rotation.y * 16
                            width: 6
                            height: 6

                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: -1
                                color: "transparent"
                                border.color: "white"
                                border.width: 1
                                opacity: rotationMouse.hovered ? 1.0 : 0.5
                                rotation: 45

                                antialiasing: false
                                smooth: false
                            }
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: -2
                                color: "transparent"
                                border.color: "black"
                                border.width: 1
                                opacity: rotationMouse.hovered ? 1.0 : 0.5
                                rotation: 45
                            }

                            MouseArea {
                                id: rotationMouse
                                anchors.fill: parent
                                anchors.margins: -3

                                property var hovered: mouseArea.isContainedBy(rotationMouse)

                                function getPosition() {
                                    var pos = rotationMouse.mapToItem(area, mouseX, mouseY)
                                    return Qt.point(pos.x/area.scale.x, pos.y/area.scale.y)
                                }

                                onPressed: {
                                    var origin = Qt.point(root.boundArea.x + root.boundArea.width/2, root.boundArea.y + root.boundArea.height/2)

                                    var pos = getPosition()

                                    var angle = Math.atan2(pos.x - origin.x, pos.y - origin.y)

                                    mouseArea.rotateOrigin = origin
                                    mouseArea.rotateStart = angle

                                    mouse.accepted = false
                                }
                            }
                        }

                        Item {
                            id: scaleNode
                            anchors.fill: parent
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: -1
                                color: "transparent"
                                border.color: "white"
                                border.width: 1
                                opacity: scaleMouse.hovered ? 1.0 : 0.5
                            }
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: -2
                                color: "transparent"
                                border.color: "black"
                                border.width: 1
                                opacity: scaleMouse.hovered ? 1.0 : 0.5
                            }
                            MouseArea {
                                id: scaleMouse
                                anchors.fill: parent
                                anchors.margins: -3

                                property var hovered: mouseArea.isContainedBy(scaleMouse)

                                function getPosition() {
                                    var pos = scaleMouse.mapToItem(area, mouseX, mouseY)
                                    return Qt.point(pos.x/area.scale.x, pos.y/area.scale.y)
                                }

                                onPressed: {
                                    var currentCorner = Qt.point(Math.max(0, node.position.x), Math.max(0, node.position.y))
                                    var currentPixel = Qt.point(bound.x + bound.width*currentCorner.x, bound.y + bound.height*currentCorner.y)
                                    var current = Qt.point(
                                        root.boundArea.x + root.boundArea.width*currentCorner.x,
                                        root.boundArea.y + root.boundArea.height*currentCorner.y
                                    )

                                    var originCorner = Qt.point(Math.max(0, -node.position.x), Math.max(0, -node.position.y))
                                    var origin = Qt.point(
                                        root.boundArea.x + root.boundArea.width*originCorner.x,
                                        root.boundArea.y + root.boundArea.height*originCorner.y
                                    )

                                    var mousePixel = scaleMouse.mapToItem(area, mouseX, mouseY)

                                    mouseArea.scaleOrigin = origin
                                    mouseArea.scaleStart = current
                                    mouseArea.scaleOffset = Qt.point(mousePixel.x - currentPixel.x, mousePixel.y - currentPixel.y)

                                    mouse.accepted = false
                                }
                            }
                        }
                    }
                }
            }

            Item {
                id: selection
                property var rect: root.selectionArea
                visible: rect != null
                x: rect != null ? rect.x * area.scale.x: 0
                y: rect != null ? rect.y * area.scale.x: 0
                width: rect != null ? rect.width * area.scale.x : 0
                height: rect != null ? rect.height * area.scale.x: 0

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -1
                    color: "white"
                    border.color: "white"
                    border.width: 1
                    opacity: 0.1
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -2
                    color: "transparent"
                    border.color: "black"
                    border.width: 1
                    opacity: 0.1
                }
            }

            SContextMenu {
                id: contextMenu
                property var childrenWidth: Math.max(newPoseMenuItem.contentWidth, deleteMenuItem.contentWidth, attachContentWidth, repairMenuItem.contentWidth, flipHMenuItem.contentWidth, flipVMenuItem.contentWidth)
                width: childrenWidth + 20
                property var position: null
                property var node: null
                property var pose: null
                x: position != null ? position.x * area.scale.x : 0
                y: position != null ? position.y * area.scale.y : 0
                property var blank: false
                property var repair: node != null && pose != null ? pose.getRepairable(node) : []

                SContextMenuItem {
                    id: newPoseMenuItem
                    width: contextMenu.width
                    visible: contextMenu.blank
                    text: "New Pose"
                    shortcut: "Ctrl+N"
                    onPressed: {
                        root.target.addPose(contextMenu.position, root.relative)
                    }
                }
                
                SContextMenuItem {
                    id: deleteMenuItem
                    width: contextMenu.width
                    visible: root.selected.length != 0 && !contextMenu.blank
                    text: root.selected.length == 1 ? "Delete " + root.selected[0].name: "Delete Selected"
                    shortcut: "Del"
                    onPressed: {
                        root.doDelete()
                    }
                }

                SMenuSeparator {
                    visible: contextMenu.repair.length != 0 || repairMenuItem.visible
                }

                SContextMenuItem {
                    id: repairMenuItem
                    width: contextMenu.width
                    visible: contextMenu.repair.length == 0 && contextMenu.pose != null && contextMenu.pose.repairAmount() != contextMenu.repair.length
                    text: "Attach All"
                    shortcut: "Ctrl+R"
                    onPressed: {
                        contextMenu.pose.attachAll(area.width/area.height)
                    }
                }

                // Repeater is screwing up ordering, do it manually
                property var attachContentWidth: Math.max(attach0MenuItem.contentWidth,attach1MenuItem.contentWidth,attach2MenuItem.contentWidth,attach3MenuItem.contentWidth,attach4MenuItem.contentWidth)

                SContextMenuItem {
                    id: attach0MenuItem
                    width: contextMenu.width
                    property var index: 0
                    property var node: contextMenu.repair.length > index ? contextMenu.repair[index] : null
                    visible: node != null
                    text: visible ? "Attach " + node.name : ""
                    shortcut: "Ctrl+R"
                    onPressed: {
                        node.attach(contextMenu.position)
                    }
                }

                SContextMenuItem {
                    id: attach1MenuItem
                    width: contextMenu.width
                    property var index: 1
                    property var node: contextMenu.repair.length > index ? contextMenu.repair[index] : null
                    visible: node != null
                    text: visible ? "Attach " + node.name : ""
                    shortcut: "Ctrl+R"
                    onPressed: {
                        node.attach(contextMenu.position)
                    }
                }

                SContextMenuItem {
                    id: attach2MenuItem
                    width: contextMenu.width
                    property var index: 2
                    property var node: contextMenu.repair.length > index ? contextMenu.repair[index] : null
                    visible: node != null
                    text: visible ? "Attach " + node.name : ""
                    shortcut: "Ctrl+R"
                    onPressed: {
                        node.attach(contextMenu.position)
                    }
                }

                SContextMenuItem {
                    id: attach3MenuItem
                    width: contextMenu.width
                    property var index: 3
                    property var node: contextMenu.repair.length > index ? contextMenu.repair[index] : null
                    visible: node != null
                    text: visible ? "Attach " + node.name : ""
                    shortcut: "Ctrl+R"
                    onPressed: {
                        node.attach(contextMenu.position)
                    }
                }

                SContextMenuItem {
                    id: attach4MenuItem
                    width: contextMenu.width
                    property var index: 4
                    property var node: contextMenu.repair.length > index ? contextMenu.repair[index] : null
                    visible: node != null
                    text: visible ? "Attach " + node.name : ""
                    shortcut: "Ctrl+R"
                    onPressed: {
                        node.attach(contextMenu.position)
                    }
                }

                SMenuSeparator {
                    visible: root.selected.length > 1
                }

                SContextMenuItem {
                    id: flipHMenuItem
                    text: "Flip Horizontally"
                    visible: root.selected.length > 1 && !contextMenu.blank
                    onPressed: {
                        for(var i = 0; i < root.selected.length; i++) {
                            root.selected[i].flip(root.boundArea, false)
                        }
                        root.doDraw()
                    }
                }
                SContextMenuItem {
                    id: flipVMenuItem
                    text: "Flip Vertically"
                    visible: root.selected.length > 1 && !contextMenu.blank
                    onPressed: {
                        for(var i = 0; i < root.selected.length; i++) {
                            root.selected[i].flip(root.boundArea, true)
                        }
                        root.doDraw()
                    }
                }
            }
        }
    }


    FileDialog {
        id: poseSaveDialog
        title: root.tr("Save pose", "General")
        nameFilters: [root.tr("Image files") + " (*.png)"]
        fileMode: FileDialog.SaveFile
        defaultSuffix: "png"
        onAccepted: {
            root.target.savePose(poseSaveDialog.file)
        }
    }

    Rectangle {
        id: poseBar
        width: 40
        height: (width-2)*2
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: -2
        color: COMMON.bg2
        border.color: COMMON.bg4
        border.width: 2

        Column {
            anchors.fill: parent
            anchors.margins: 2

            SIconButton {
                width: parent.width
                height: width
                inset: 4
                icon: root.relative ? "qrc:/icons/rotate.svg" : "qrc:/icons/translate.svg"
                tooltip: root.relative ? "Switch to Translation mode (Alt)" : "Switch to Rotation mode (Alt)"
                color: "transparent"
                onPressed: {
                    target.relativePosing = !target.relativePosing
                }
            }

            SIconButton {
                width: parent.width
                height: width
                inset: 12
                icon: "qrc:/icons/save.svg"
                tooltip: "Export pose image"
                color: "transparent"
                onPressed: {
                    poseSaveDialog.open()
                }
            }
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_A:
                root.doSelectAll()
                break;
            case Qt.Key_F:
                root.doRepair()
                break;
            case Qt.Key_Z:
                root.target.undoPose()
                break;
            case Qt.Key_Y:
                root.target.redoPose()
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            case Qt.Key_Escape:
                if(mouseArea.active()) {
                    root.doClear(false)
                } else {
                    root.doClear(true)
                    root.close()
                }
                break;
            case Qt.Key_Alt:
                target.relativePosing = !target.relativePosing
                break;
            case Qt.Key_Delete:
                root.doDelete()
            default:
                event.accepted = false
                break;
            }
        }
    }
}
