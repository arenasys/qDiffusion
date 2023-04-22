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

    contentItem: Rectangle {
        implicitWidth: 6
        implicitHeight: 200
        color: control.pressed ? control.pressedColor : control.color
        // Hide the ScrollBar when it's not needed.
        opacity: control.policy === ScrollBar.AlwaysOn || (control.active && control.size < 1.0) ? 0.75 : 0

        // Animate the changes in opacity (default duration is 250 ms).
        Behavior on opacity {
            NumberAnimation {}
        }
    }
}