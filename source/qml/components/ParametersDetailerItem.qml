import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"

Item {
    id: root
    height: 30
    signal settings()
    signal deactivate()

    property var label: "Label"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0

        color: COMMON.bg3
        border.color: COMMON.bg4

        MouseArea {
            id: mouseArea
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: -2
            anchors.leftMargin: 0
            hoverEnabled: true
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onPressed: {
                if (mouse.button === Qt.LeftButton) {
                    root.forceActiveFocus()
                    mouseArea.update()
                } else if (mouse.button === Qt.RightButton) {
                    root.deactivate()
                }
            }
        }
        SText {
            anchors.right: settingsButton.left
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 7

            text: root.label
            pointSize: root.mini ? 7.7 : 9.6
            color: COMMON.fg0
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        SIconButton {
            id: settingsButton
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 2
            anchors.rightMargin: 6
            width: height
            inset: 4
            icon: "qrc:/icons/ellipsis.svg"

            onPressed: {
                root.settings()
            }
        }
    }

    Rectangle {
        visible: root.activeFocus
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0

        color: "transparent"
        border.color: COMMON.bg7
    }

    Keys.onPressed: {
        event.accepted = true
        switch(event.key) {
        case Qt.Key_Delete:
            root.deactivate()
            break;
        default:
            event.accepted = false
            break;
        }
    }
}