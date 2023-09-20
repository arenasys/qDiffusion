import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ScrollBar {
    id: control
    size: 0.3
    position: 0.2
    active: true
    orientation: Qt.Vertical
    property var color: COMMON.bg7
    property var pressedColor: COMMON.fg3
    property var barWidth: 6
    property var barHeight: 200

    contentItem: Rectangle {
        implicitWidth: control.barWidth * 2
        implicitHeight: parent.barHeight
        color: "transparent"

        Rectangle {
            height: parent.height
            width: control.barWidth
            anchors.right: parent.right
            color: control.pressed ? control.pressedColor : control.color
            opacity: control.policy === ScrollBar.AlwaysOn || (control.active && control.size < 1.0) ? 0.75 : 0
        }
    }
}