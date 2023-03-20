import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Rectangle {
    id: root
    property var working: false
    property var progress: -1
    property var info: ""
    property var hue: 0.0
    property var label: null
    property var isHovered: mouseArea.containsMouse && !working && !disabled
    property var isPressed: mouseArea.containsPress && !working && !disabled
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

    Rectangle {
        visible: root.progress >= 0.0
        id: genProgress
        x: -10
        y: 2
        height: root.height * 4
        width: (root.width * root.progress) + 15
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        rotation: -15
        antialiasing: true
    }

    function wrap(x) {
        while(x > 1.5*root.width) {
            x -= 2*root.width;
        }
        return x
    }

    Rectangle {
        visible: root.working && root.progress < 0.0
        id: genWorking
        property var offset: root.width
        x: offset-25
        y: 2
        height: parent.height * 2
        width: 50
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        rotation: -15
        opacity: 0.35
        antialiasing: true

        RotationAnimation on offset {
            id: offsetAnimation
            duration: 1200
            loops: Animation.Infinite
            from: 0
            to: root.width
        }
    }

    Rectangle {
        visible: genWorking.visible
        property var offset: wrap(genWorking.offset + root.width)
        x: offset-25
        y: genWorking.y
        height: genWorking.height
        width: genWorking.width
        color: genWorking.color
        rotation: genWorking.rotation
        opacity: genWorking.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        visible: genWorking.visible
        property var offset: wrap(genWorking.offset - root.width/2)
        x: offset-25
        y: genWorking.y
        height: genWorking.height
        width: genWorking.width
        color: genWorking.color
        rotation: genWorking.rotation
        opacity: genWorking.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        visible: genWorking.visible
        property var offset: wrap(genWorking.offset + root.width/2)
        x: offset-25
        y: genWorking.y
        height: genWorking.height
        width: genWorking.width
        color: genWorking.color
        rotation: genWorking.rotation
        opacity: genWorking.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.width: 2
        border.color: Qt.lighter(parent.color, 1.15)
    }

    SText {
        anchors.fill: parent
        text: root.working ? (mouseArea.containsMouse && root.info != "" ? root.info : "Working...") : "Generate"
        color: Qt.lighter(COMMON.fg0, mouseArea.containsPress ? 0.85 : 1.0)
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    Rectangle {
        anchors.fill: parent
        color: root.disabled && !root.working ? "#90101010" : "transparent"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if(root.disabled)
                return
            if (mouse.button === Qt.LeftButton) {
                root.pressed()
            } else {
                root.contextMenu()
            }
        }
    }
}