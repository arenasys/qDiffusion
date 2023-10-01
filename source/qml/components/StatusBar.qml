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

    Item {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 2
    
        Rectangle {
            id: statusColor
            anchors.fill: parent
            color: GUI.statusProgress <= 0 ? [COMMON.accent(0.2), COMMON.accent(0.4), COMMON.accent(0.6), "#a0000000", "#a0000000"][GUI.statusMode] : Qt.lighter(COMMON.accent(0), 0.75)
        }

        Rectangle {
            width: parent.width * GUI.statusProgress
            height: 2
            color: Qt.lighter(statusColor.color, 2)
        }

        Rectangle {
            anchors.fill: parent
            opacity: 0.25
            color: COMMON.bg0
        }
    }

    SText {
        anchors.fill: parent
        anchors.topMargin: 2
        anchors.bottomMargin: 4
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        text: TRANSLATOR.instance.translate(GUI.statusText, "Status")
        font.bold: true
        pointSize: 9.8
        color: COMMON.fg1_5
    }
}