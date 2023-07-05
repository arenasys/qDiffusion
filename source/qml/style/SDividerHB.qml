import QtQuick 2.15

import gui 1.0

Rectangle {
    id: root
    anchors.left: parent.left
    anchors.right: parent.right
    required property int minOffset
    required property int maxOffset
    required property int offset
    y: snapping ? (parent.height - Math.floor(snap)) : (parent.height - offset)
    height: 5
    color: COMMON.bg4
    property bool locked: true
    property bool snapping: false
    property var snap: null
    property var wasSnapped: false
    property var startOffset: 0
    property var snapSize: 50
    property var overflow: 0

    onOffsetChanged: {
        if(snap - offset == 0.0) {
            root.offset = Qt.binding(function() {return snap})
            root.locked = true
        }
    }

    MouseArea {
        anchors.fill: parent
        anchors.topMargin: -root.overflow
        anchors.bottomMargin: -root.overflow

        hoverEnabled: true
        onPositionChanged: {
            if(pressedButtons) {
                root.locked = false
                parent.offset = Math.min(parent.maxOffset, Math.max(parent.minOffset, root.parent.height - (parent.y + mouseY)))
                if(snap != null) {
                    if(!root.wasSnapped) {
                        root.snapping = (Math.abs(snap - offset) < snapSize)
                    } else if (Math.abs(root.startOffset - offset) > snapSize) {
                        root.wasSnapped = false
                    }
                }
            }
        }
        onPressed: {
            root.startOffset = offset
            root.wasSnapped = (Math.abs(snap - offset) == 0)
        }
        onReleased: {
            if(snap == null) {
                return
            }
            root.snapping = false
            if(Math.abs(snap - offset) < snapSize) {
                root.offset = Qt.binding(function() {return snap})
                root.locked = true
            }
        }
    }

    onMaxOffsetChanged: {
        if(!root.locked && parent && parent.height > 0 && y > 0)
            offset = Math.min(maxOffset, Math.max(minOffset, offset))
    }
}