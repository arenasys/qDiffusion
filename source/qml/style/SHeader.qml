import QtQuick 2.15

import gui 1.0

Item {
    id: root
    anchors.left: parent.left
    anchors.right: parent.right
    required property var text
    property var hasDivider: true

    height: header.height + divider.height

    Rectangle {
        id: divider
        color: COMMON.bg4
        height: hasDivider ? 5 : 0
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
    }

    Rectangle {
        id: header
        color: COMMON.bg3
        height: 30
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: hasDivider ? divider.bottom : parent.top
        SText {
            text: root.text
            pointSize: 11
            leftPadding: 8
            rightPadding: 16
            font.bold: false
            color: "white"
            verticalAlignment: Text.AlignVCenter
            width: Math.min(parent.width, implicitWidth)
            elide: Text.ElideRight
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }
    }
}
