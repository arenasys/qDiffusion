import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Rectangle {
    id: root
    property var working: false
    property var progress: -1
    property var info: ""
    property var remaining: 0

    property var text: "Generate"

    function tr(str, file = "GenerateButton.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    property var hue: 0.0
    property var label: null
    property var isHovered: mouseArea.containsMouse && !working && !disabled
    property var isPressed: mouseArea.down && !working && !disabled
    property var disabled: false

    signal pressed();
    signal contextMenu();

    color: Qt.lighter(COMMON.accent(hue), (root.isHovered ? (root.isPressed ? 0.85 : 1.15) : 1))
    clip: true

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        color: COMMON.bg2
    }

    
    SProgress {
        anchors.fill: parent
        progress: root.progress
        working: root.working
        duration: 1200
        color: root.color
    }

    Rectangle {
        visible: remainingLabel.visible
        anchors.fill: remainingLabel
        width: 15
        height: 15
        color: COMMON.bg2
        border.color: parent.color
        border.width: 2
    }

    SText {
        visible: root.remaining >= 1
        id: remainingLabel
        anchors.top: parent.top
        anchors.right: parent.right
        text: root.remaining
        pointSize: 9
        font.bold: true
        rightPadding: 5
        leftPadding: 3
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.width: 2
        border.color: Qt.lighter(parent.color, 1.15)
    }

    SText {
        anchors.fill: parent
        text: root.working ? (mouseArea.containsMouse && root.info != "" ? root.info : root.tr("Working...")) : root.tr(root.text)
        color: Qt.lighter(COMMON.fg0, mouseArea.down ? 0.85 : 1.0)
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    Rectangle {
        anchors.fill: parent
        color: root.disabled && !root.working ? "#a0101010" : "transparent"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property var down: false
        onPressed: {
            if (!root.disabled && mouse.button === Qt.LeftButton) {
                mouseArea.down = true
                root.pressed()
            }
            if (mouse.button === Qt.RightButton) {
                root.contextMenu()
            }
        }
        onReleased: {
            if (mouse.button === Qt.LeftButton) {
                mouseArea.down = false
            }
        }
    }
}