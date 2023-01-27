import QtQuick 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: thumb

    property string source
    property bool selected

    signal select()
    signal open()
    signal contextMenu()

    RectangularGlow {
        anchors.fill: overlay
        visible: overlay.visible
        glowRadius:  selected ? 6 : 10
        opacity: 0.5
        spread: 0.2
        color: selected ? "white" : "black"
        cornerRadius: 10
    }

    LoadingSpinner {
        height: thumb.height/4
        width: thumb.width/4
        anchors.centerIn: thumb
        running: img.status !== Image.Ready
    }

    Image {
        id: img
        anchors.fill: thumb
        asynchronous: false
        source: "image://async-thumbnail/" + thumb.source
        fillMode: Image.PreserveAspectFit
        mipmap: true
        cache: false
    }

    Rectangle {
        id: overlay
        visible: img.status == Image.Ready
        x: img.x + Math.max(0, Math.floor((img.width - img.paintedWidth) / 2))
        y: img.y + Math.max(0, Math.floor((img.height - img.paintedHeight) / 2))
        width: Math.min(img.width, img.paintedWidth)
        height: Math.min(img.height, img.paintedHeight)
        color: thumbMouse.containsMouse ? "#50ffffff" : "#00000000"

        MouseArea {
            id: thumbMouse
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onPressed: {
                thumb.select()
                if (mouse.button === Qt.RightButton) {
                    thumb.contextMenu()
                    return
                }
                if(mouse.flags === Qt.MouseEventCreatedDoubleClick && count > 0) {
                    thumb.open()
                }
            }
        }
    }
}