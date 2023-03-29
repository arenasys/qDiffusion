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
        implicitHeight: 6
        color: control.pressed ? COMMON.fg3 : COMMON.bg7
        // Hide the ScrollBar when it's not needed.
        opacity: control.policy === ScrollBar.AlwaysOn || (control.active && control.size < 1.0) ? 0.75 : 0

        // Animate the changes in opacity (default duration is 250 ms).
        Behavior on opacity {
            NumberAnimation {}
        }
    }
}