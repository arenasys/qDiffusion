import QtQuick 2.15

import gui 1.0

Item {
    id: root

    property var progress: 0.0
    property var working: false
    property var duration: 1000
    property var barWidth: 50
    property var color: COMMON.bg4
    property var count: 3

    function wrap(x) {
        if(root.width <= 0) {
            return x
        }

        while(x > (root.count/(root.count-1))*root.width) {
            x -= ((root.count+1)/(root.count-1))*root.width;
        }
        return x
    }

    Rectangle {
        id: progressBar
        visible: root.progress >= 0.0
        height: root.height
        width: Math.floor((root.width * root.progress) - height*0.85)
        color: root.color
    }

    Item {
        anchors.left: progressBar.right
        anchors.verticalCenter: parent.verticalCenter
        height: root.height * 2
        width: height
        clip: true

        Rectangle {
            visible: root.progress >= 0.0
            anchors.horizontalCenter: parent.left
            anchors.verticalCenter: parent.verticalCenter
            height: parent.height
            width: height
            color: root.color
            rotation: -15
            antialiasing: true
        }
    }

    Rectangle {
        visible: root.working && root.progress < 0.0
        id: working
        property var percent: offsetAnimation.value
        property var offset: percent * root.width
        x: offset-25
        y: -parent.height / 2
        height: parent.height * 2
        width: root.barWidth
        color: parent.color
        anchors.verticalCenter: parent.verticalCenter
        rotation: -15
        opacity: 0.35
        antialiasing: true

        SAnimation {
            id: offsetAnimation
            running: working.visible
            minValue: 0
            maxValue: 1
            duration: Math.max(100, root.duration)
            fps: 30
            loop: true
        }
    }

    Repeater {
        anchors.fill: parent
        model: root.count
        delegate: Rectangle {
        visible: working.visible
            property var offset: wrap(working.offset + (index+1)*root.width/(root.count-1))
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
}