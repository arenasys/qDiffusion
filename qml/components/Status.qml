import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    anchors.margins: 2
    clip: true
    Rectangle {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: Math.max(100, parent.width)

        color: "transparent"
        border.width: 2
        border.color: [COMMON.accent(0.2), COMMON.accent(0.4), COMMON.accent(0.6), "#a0000000"][GUI.statusMode]

        SText {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: GUI.statusText
            font.bold: true
        }
    }
}
