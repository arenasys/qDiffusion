import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Rectangle {
    id: button
    color: COMMON.bg3
    property var icon
    property var iconColor: COMMON.bg6
    property var iconHoverColor: COMMON.fg0
    property bool disabled: false
    property bool working: false
    property var inset: 10
    property var tooltip: ""
    property var hovered: false
    height: 35
    width: 35
    
    signal pressed();
    signal contextMenu();
    signal entered();
    signal exited();

    MouseArea {
        anchors.fill: parent
        id: mouse
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onPressed: {
            if(disabled)
                return
            if (mouse.button === Qt.LeftButton) {
                button.pressed()
            } else {
                button.contextMenu()
            }
            
        }

        onEntered: {
            button.entered()
        }

        onExited: {
            button.exited()
        }
    }

    SToolTip {
        id: infoToolTip
        visible: !disabled && tooltip != "" && mouse.containsMouse
        delay: 100
        text: tooltip
    }

    Image {
        id: img
        source: icon
        width: parent.height - inset
        height: width
        sourceSize: Qt.size(parent.width, parent.height)
        anchors.centerIn: parent
    }

    ColorOverlay {
        id: color
        anchors.fill: img
        source: img
        color: disabled ? Qt.darker(iconColor) : (mouse.containsMouse ? iconHoverColor : iconColor)
    }
}
