import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

MenuItem {
    id: menuItem
    implicitWidth: 150
    implicitHeight: menuItemSize
    hoverEnabled: true
    //font.bold: true
    font.pointSize: 10.5

    property real menuItemSize: 20

    indicator: Item {
        implicitWidth: menuItemSize
        implicitHeight: menuItemSize
        Rectangle {
            width: 16
            height: 16
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 6
            visible: menuItem.checkable
            radius: 3
            color: COMMON.bg6

            border.color: COMMON.bg5
            border.width: 3

            Image {
                id: img
                width: 16
                height: 16
                visible:  menuItem.checked
                anchors.centerIn: parent
                source: "qrc:/icons/tick.svg"
                sourceSize: Qt.size(parent.width, parent.height)
            }

            ColorOverlay {
                id: color
                visible:  menuItem.checked
                anchors.fill: img
                source: img
                color: COMMON.fg2
            }
        }
    }

    contentItem: SText {
        leftPadding: menuItem.checkable ? menuItem.indicator.width : 0
        text: menuItem.text
        font: menuItem.font
        color: COMMON.fg0
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        implicitWidth: 150
        implicitHeight: menuItemSize
        color: menuItem.hovered ? COMMON.bg5 : "transparent"
    }
}