import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    property alias label: labelText.text
    property var disabled: false

    signal pressed()
    width: 100
    height: 30

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        color: mouseArea.containsPress && !root.disabled ? COMMON.bg4 : COMMON.bg3
        border.color: mouseArea.containsMouse && !root.disabled ? COMMON.bg5 : COMMON.bg4

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true

            onPressed: {
                if(!root.disabled) {
                    root.pressed()
                }
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

        Rectangle {
            anchors.fill: parent
            visible: root.disabled
            color: "#c0101010"
        }
    }


}