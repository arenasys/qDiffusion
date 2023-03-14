import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    required property var text
    property var collapsable: true
    property var isCollapsed: false
    property var hasDivider: true
    property var hasSides: false
    signal expanded()
    signal collapsed()

    onIsCollapsedChanged: {
        indicator.requestPaint()
    }

    default property alias content: column.children
    implicitHeight: header.height + column.height + (hasDivider ? 5 : 0) - (isCollapsed ? 2 : 0)

    property var contentMargin: hasSides ? 3 : 0

    Rectangle {
        id: header
        color: COMMON.bg3
        height: 30
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.top: parent.top
        SText {
            text: root.text
            font.pointSize: 11
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

        Canvas {
            id: indicator
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: height
            visible: root.collapsable
            onPaint: {
                var context = getContext("2d");
                var ox = width/2
                var oy = height/2
                var dx = 5
                var dy = root.isCollapsed ? dx : -dx

                context.reset();
                context.moveTo(ox-dx, oy-dy);
                context.lineTo(ox+dx, oy-dy);
                context.lineTo(ox, oy+dy);
                context.closePath();
                context.fillStyle = COMMON.bg6;
                context.fill();
            }

            MouseArea {
                id: canvasMouseArea
                anchors.fill: parent
                onPressed: {
                    if(!root.collapsable) {
                        return;
                    }
                    root.isCollapsed = !root.isCollapsed
                    if(root.isCollapsed) {
                        root.collapsed()
                    } else {
                        root.expanded()
                    }
                }
            }
        }
    }
    Column {
        id: column
        visible: !isCollapsed
        height: isCollapsed ? 0 : undefined
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: root.contentMargin
        anchors.rightMargin: root.contentMargin
    }

    Rectangle {
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        height: hasDivider ? 3 : 0
        color: COMMON.bg4
    }

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: hasSides ? 3 : 0
        color: COMMON.bg4
    }

    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: hasSides ? 3 : 0
        color: COMMON.bg4
    }
}