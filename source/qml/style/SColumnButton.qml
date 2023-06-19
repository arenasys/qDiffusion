import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    property alias label: labelText.text
    property var active: false
    property var mini: height < 30

    signal pressed()
    signal contextMenu()
    
    width: 150
    height: 35

    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 4
        anchors.leftMargin: -1
        anchors.rightMargin: -1

        color: mini ? (active ? COMMON.bg2_5 : COMMON.bg1) : (active ? COMMON.bg4 : COMMON.bg1)

        border.color: active ? COMMON.bg5 : COMMON.bg2

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            anchors.topMargin: 0
            anchors.bottomMargin: -4
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onPressed: {
                if(mouse.button == Qt.LeftButton) {
                    root.pressed()
                } else {
                    root.contextMenu()
                }
            }
        }

        SText {
            id: labelText
            text: "Button"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            anchors.fill: parent
            font.pointSize: 10.8
            opacity: active ? 1 : 0.7
            color: COMMON.fg1
        }

        DropArea {
            anchors.fill: parent
            Timer {
                id: dragTimer
                interval: 200
                onTriggered: {
                    root.pressed()
                }
            }
            onEntered: {
                dragTimer.start()
            }
            onExited: {
                dragTimer.stop()
            }
        }
    }
}