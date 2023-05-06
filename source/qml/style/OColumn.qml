import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: root
    required property var text
    property var collapsable: true
    property var isCollapsed: false
    property var hasDivider: true
    property var padding: true
    signal expanded()
    signal collapsed()

    onIsCollapsedChanged: {
        indicator.requestPaint()
    }

    default property alias content: column.children
    implicitHeight: header.height + column.height + (padding ? (hasDivider ? 5 : 0) - (isCollapsed ? 2 : 0) : 3)

    property var contentMargin: 7

    property alias input: inputLoader.sourceComponent

    Rectangle {
        id: header
        color: COMMON.bg2_5
        height: 30
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.top: parent.top
        
        SText {
            id: labelText
            text: root.text
            font.weight: Font.Medium
            font.pointSize: 10.5
            leftPadding: 6
            rightPadding: 16
            color: COMMON.fg0
            opacity: 0.95
            verticalAlignment: Text.AlignVCenter
            width: Math.min(parent.width, implicitWidth+10)
            elide: Text.ElideRight
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        Loader {
            id: inputLoader
            anchors.right: indicator.left
            anchors.top: parent.top

            sourceComponent: Item {}
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
        Glow {
            opacity: 0.5
            anchors.fill: indicator
            radius: 2
            samples: 8
            color: COMMON.bg0
            source: indicator
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
}