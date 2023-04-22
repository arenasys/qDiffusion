import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Rectangle {
    visible: height != 0
    color: COMMON.bg0

    Rectangle {
        width: parent.width
        height: 2
        color: COMMON.bg4
    }
    
    Rectangle {
        id: statusColor
        anchors.bottom: parent.bottom
        width: parent.width
        height: 2
        color: GUI.statusProgress <= 0 ? [COMMON.accent(0.2), COMMON.accent(0.4), COMMON.accent(0.6), "#a0000000", "#a0000000"][GUI.statusMode] : COMMON.accent(0)
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width * GUI.statusProgress
        height: 2
        color: Qt.lighter(statusColor.color, 1.5)
    }

    SText {
        anchors.fill: parent
        anchors.topMargin: 2
        anchors.bottomMargin: 3
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        text: GUI.statusText
        font.bold: true
        font.pointSize: 9.8
    }
}