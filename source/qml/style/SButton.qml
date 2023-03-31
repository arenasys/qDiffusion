import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    property alias label: labelText.text

    signal pressed()
    width: 100
    height: 30

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        color: mouseArea.containsPress ? COMMON.bg4 : COMMON.bg3
        border.color: mouseArea.containsMouse ? COMMON.bg5 : COMMON.bg4

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true

            onPressed: {
                root.pressed()
            }
        }

        SText {
            id: labelText
            text: "Button"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            anchors.fill: parent
            font.pointSize: 9.8
            color: COMMON.fg1
        }
    }
}