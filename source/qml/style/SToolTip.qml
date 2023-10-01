import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ToolTip {
    id: control
    property alias pointSize: text.pointSize 
    contentItem: SText {
        id: text
        text: control.text
        pointSize: 10
        color: "white"
    }

    background: Rectangle {
        color: "#e0101010"
        border.width: 1
        border.color: COMMON.bg3
    }
}
