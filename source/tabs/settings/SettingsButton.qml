import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property alias label: labelText.text
    property var active: false

    signal pressed()
    width: 150
    height: 35

    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 4
        anchors.leftMargin: -1
        anchors.rightMargin: -1

        color: active ? COMMON.bg4 : COMMON.bg1

        border.color: active ? COMMON.bg5 : COMMON.bg2

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true

            onPressed: {
                root.pressed()
            }
        }

        SText {
            id: labelText
            text: "Button"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            anchors.fill: parent
            font.pointSize: 10.8
            color: COMMON.fg1
        }
    }
}