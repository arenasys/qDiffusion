import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Rectangle {
    id: root
    property var node
    property var scale
    property var point: node.point
    property var selected: false
    property var hovered: false

    visible: !node.isNull
    x: (point.x * scale.x) - (width/2)
    y: (point.y * scale.y) - (height/2)
    width: 8
    height: 8
    radius: 4
    color: node.color

    Rectangle {
        anchors.fill: parent
        anchors.margins: -6
        color: "transparent"
        border.width: 2
        border.color: "white"
        radius: width/2
        visible: root.selected || root.hovered
        opacity: !root.selected ? 0.5 : 1.0
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: -4
        color: "transparent"
        border.width: 2
        border.color: "black"
        radius: width/2
        visible: root.selected || root.hovered 
        opacity: !root.selected ? 0.5 : 1.0
    }
}