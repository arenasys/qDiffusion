import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    property var size: Math.max(root.width, root.height) / 4
    property var running
    visible: running
    property var source: "qrc:/icons/loading.svg"
    property var duration: 1000

    Image {
        opacity: 0.5
        id: spinner
        source: root.source
        width: root.size
        height: root.size
        sourceSize: Qt.size(width, height)
        anchors.centerIn: parent
        smooth: true
        antialiasing: true   
    }

    RotationAnimator {
        target: spinner
        loops: Animation.Infinite
        from: 0
        to: 360
        duration: root.duration
        running: true
    }
}