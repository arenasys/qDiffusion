import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ScrollBar {
    id: control
    size: 0.3
    position: 0.2
    active: true
    orientation: Qt.Horizontal

    property var totalLength: 1
    property var incrementLength: totalLength / 10
    property var showLength: 0
    property var showing: showLength == 0 || (totalLength > showLength)
    property var increment: 1/Math.ceil(totalLength/incrementLength)

    policy: showing ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
    stepSize: increment

    function doIncrement(delta) {
        var p = Math.abs(delta)/120
        if(p == 0) {
            return
        }
        stepSize = increment * p
        if(delta < 0) {
            increase()
        } else {
            decrease()
        }
        stepSize = increment
    }

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