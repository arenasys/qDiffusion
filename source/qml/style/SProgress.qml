import QtQuick 2.15

import gui 1.0

Item {
    id: root

    property var progress: 0.0
    property var working: false
    property var duration: 1000
    property var barWidth: 50
    property var color: COMMON.bg4

    function wrap(x) {
        if(root.width <= 0) {
            return x
        }

        while(x > 1.5*root.width) {
            x -= 2*root.width;
        }
        return x
    }

    Rectangle {
        visible: root.progress >= 0.0
        id: progress
        x: -10
        y: 2
        height: root.height * 4
        width: (root.width * root.progress) + 15
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        rotation: -15
        antialiasing: true
    }

    Rectangle {
        visible: root.working && root.progress < 0.0
        id: working
        property var percent: 0
        property var offset: percent * root.width
        x: offset-25
        y: 2
        height: parent.height * 2
        width: root.barWidth
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        rotation: -15
        opacity: 0.35
        antialiasing: true

        RotationAnimation on percent {
            id: offsetAnimation
            duration: root.duration
            loops: Animation.Infinite
            from: 0
            to: 1
        }
    }

    Rectangle {
        visible: working.visible
        property var offset: wrap(working.offset + root.width)
        x: offset-25
        y: working.y
        height: working.height
        width: working.width
        color: working.color
        rotation: working.rotation
        opacity: working.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        visible: working.visible
        property var offset: wrap(working.offset - root.width/2)
        x: offset-25
        y: working.y
        height: working.height
        width: working.width
        color: working.color
        rotation: working.rotation
        opacity: working.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        visible: working.visible
        property var offset: wrap(working.offset + root.width/2)
        x: offset-25
        y: working.y
        height: working.height
        width: working.width
        color: working.color
        rotation: working.rotation
        opacity: working.opacity
        antialiasing: true
        anchors.verticalCenter: parent.verticalCenter
    }
}