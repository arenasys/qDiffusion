import QtQuick 2.15

import gui 1.0

Rectangle {
    id: root
    anchors.left: parent.left
    anchors.right: parent.right
    required property int minOffset
    required property int maxOffset
    required property int offset
    y: parent.height - offset
    height: 5
    color: COMMON.bg4

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: {
            if(pressedButtons) {
                parent.offset = Math.min(parent.maxOffset, Math.max(parent.minOffset, root.parent.height - (parent.y + mouseY)))
            }
        }
    }

    onMaxOffsetChanged: {
        if(parent && parent.height > 0 && y > 0)
            offset = Math.min(maxOffset, Math.max(minOffset, offset))
    }
}