import QtQuick 2.15

import gui 1.0

Rectangle {
    id: root
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    required property int minOffset
    required property int maxOffset
    required property int offset
    x: offset
    width: 5
    color: COMMON.bg4
    property var limited: false
    function setLimited(current) {
        if(current != limited) {
            limited = current
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        property var startPosition: Qt.point(0,0)
        onPressed: {
            startPosition = Qt.point(mouse.x, mouse.y)
            root.setLimited(false)
        }
        onReleased: {
            root.setLimited(false)
        }
        onPositionChanged: {
            if(pressedButtons) {
                parent.offset = Math.min(parent.maxOffset, Math.max(parent.minOffset, parent.x + mouseX))

                var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                if(parent.offset == parent.maxOffset && Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 400) {
                    root.setLimited(true)
                } else {
                    root.setLimited(false)
                }
            }
        }
    }

    onMaxOffsetChanged: {
        offset = Math.min(maxOffset, Math.max(minOffset, offset))
    }
}