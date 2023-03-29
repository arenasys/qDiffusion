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
            id: endpointText
            visible: parent.height > 60
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 25
            topPadding: 8
            leftPadding: 8
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            text: GUI.remoteEndpoint
            font.bold: true
            color: COMMON.fg2
        }

        SText {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top:  endpointText.visible ? endpointText.bottom : parent.top
            anchors.bottom: parent.bottom
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            bottomPadding: endpointText.visible ? 5 : 0
            text: GUI.statusText
            font.bold: true
        }
    }
}
