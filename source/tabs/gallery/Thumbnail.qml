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
    signal drag()

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
        anchors.fill: thumb
        running: img.status !== Image.Ready
    }

    Timer {
        interval: 200
        running: true
        onTriggered: {
            img.fullDelay = false
        }
    }

    Timer {
        interval: 10
        running: true
        onTriggered: {
            img.cacheDelay = false
        }
    }

    Image {
        id: img
        property var fullDelay: true
        property var cacheDelay: true

        anchors.top: thumb.top
        anchors.left: thumb.left
        anchors.right: thumb.right
        anchors.bottom: thumb.bottom

        anchors.leftMargin: thumb.padding
        anchors.topMargin: thumb.padding

        source: GUI.isCached(thumb.source) ? (cacheDelay ? "" : ("image://sync/" + thumb.source)) : (fullDelay ? "" : ("image://async/" + thumb.source))
        fillMode: Image.PreserveAspectFit
        cache: false
    }

    Rectangle {
        anchors.fill: overlay
        anchors.margins: -1
        color: "transparent"
        border.color: "black"
        border.width: selected || multiSelected ? 1 : 0
        visible: img.status == Image.Ready
    }

    Rectangle {
        anchors.fill:overlay
        anchors.margins: 0
        color: "transparent"
        border.color: "#cc2f00"
        border.width: selected || multiSelected ? 2 : 0
        visible: img.status == Image.Ready
    }

    Rectangle {
        anchors.fill:overlay
        anchors.margins: 2
        color: "transparent"
        border.color: "black"
        border.width: selected || multiSelected ? 1 : 0
        visible: img.status == Image.Ready
    }


    Rectangle {
        id: overlay
        visible: img.status == Image.Ready
        x: img.x + Math.max(0, Math.floor((img.width - img.paintedWidth) / 2))
        y: img.y + Math.max(0, Math.floor((img.height - img.paintedHeight) / 2))
        width: Math.min(img.width, img.paintedWidth)
        height: Math.min(img.height, img.paintedHeight)
        color: "#00000000"

        MouseArea {
            id: thumbMouse
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property var startPosition: null

            onPressed: {
                if (mouse.button == Qt.LeftButton) {
                    if (mouse.modifiers & Qt.ControlModifier) {
                        thumb.controlSelect()
                    } else if (mouse.modifiers & Qt.ShiftModifier) {
                        thumb.shiftSelect()
                    } else {
                        startPosition = Qt.point(mouse.x, mouse.y)
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

            onReleased: {
                startPosition = null
            }

            onPositionChanged: {
                if(pressed && startPosition) {
                    var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                    if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5) {
                        thumb.drag()
                        startPosition = null
                    }
                }
            }
        }
    }
}