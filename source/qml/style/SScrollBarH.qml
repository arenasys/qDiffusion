import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ScrollBar {
    id: control
    size: 0.3
    position: 0.2
    active: true
    orientation: Qt.Horizontal

    contentItem: Rectangle {
        implicitWidth: 200
        implicitHeight: 12
        color: "transparent"

        Rectangle {
            width: parent.width
            height: 6
            anchors.bottom: parent.bottom

            color: control.pressed ? COMMON.fg3 : COMMON.bg7
            opacity: control.policy === ScrollBar.AlwaysOn || (control.active && control.size < 1.0) ? 0.75 : 0
        }
    }
}