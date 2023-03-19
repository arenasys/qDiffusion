import QtQuick 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: thumb

    property string source
    property bool selected
    property bool multiSelected
    property int padding
    property int border: selected || multiSelected ? 2 : 0

    signal select()
    signal controlSelect()
    signal shiftSelect()
    signal open()
    signal contextMenu()

    RectangularGlow {
        anchors.fill: overlay
        visible: overlay.visible
        glowRadius:  selected ? 6 : 10
        opacity: 0.5
        spread: 0.2
        color: "black"//selected || multiSelected ? "white" : "black"
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
        anchors.top: thumb.top
        anchors.left: thumb.left
        anchors.right: thumb.right
        anchors.bottom: thumb.bottom

        anchors.leftMargin: thumb.padding
        anchors.topMargin: thumb.padding

        source: (GUI.isCached(thumb.source) ? "image://sync/" : "image://async/") + thumb.source
        fillMode: Image.PreserveAspectFit
        cache: false
    }

    Rectangle {
        anchors.fill:img
        color: "transparent"
        border.color: "white"
        border.width: thumb.border
    }

    Rectangle {
        id: overlay
        visible: img.status == Image.Ready
        x: img.x + Math.max(0, Math.floor((img.width - img.paintedWidth) / 2))
        y: img.y + Math.max(0, Math.floor((img.height - img.paintedHeight) / 2))
        width: Math.min(img.width, img.paintedWidth)
        height: Math.min(img.height, img.paintedHeight)
        color: thumbMouse.containsMouse ? "#30ffffff" : "#00000000"

        MouseArea {
            id: thumbMouse
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onPressed: {
                if (mouse.button == Qt.LeftButton) {
                    if (mouse.modifiers & Qt.ControlModifier) {
                        thumb.controlSelect()
                    } else if (mouse.modifiers & Qt.ShiftModifier) {
                        thumb.shiftSelect()
                    } else {
                        thumb.select()
                    }
                }
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