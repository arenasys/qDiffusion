import QtQuick 2.15

import gui 1.0

Rectangle {
    id: root
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    required property int minOffset
    required property int maxOffset
    required property int offset
    x: parent.width - offset
    width: 5
    color: COMMON.bg4
    property bool locked: true
    property var snap: null

    onOffsetChanged: {
        if(snap - offset == 0.0) {
            root.offset = Qt.binding(function() {return snap})
            root.locked = true
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: {
            if(pressedButtons) {
                root.locked = false
                parent.offset = Math.min(parent.maxOffset, Math.max(parent.minOffset, root.parent.width - (parent.x + mouseX)))
            }
        }
        onReleased: {
            if(snap == null) {
                return
            }
            if(Math.abs(snap - offset) < 50) {
                root.offset = Qt.binding(function() {return snap})
                root.locked = true
            }
        }
    }

    onMaxOffsetChanged: {
        if(!root.locked && parent && parent.width > 0 && x > 0)
            offset = Math.min(maxOffset, Math.max(minOffset, offset))
    }
}