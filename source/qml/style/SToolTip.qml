import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ToolTip {
    id: control
    font.pointSize: 10
    contentItem: SText {
        text: control.text
        font: control.font
        color: "white"
    }

    background: Rectangle {
        color: "#e0101010"
        border.width: 1
        border.color: COMMON.bg3
    }
}
