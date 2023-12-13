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