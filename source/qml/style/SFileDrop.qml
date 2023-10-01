import QtQuick 2.15
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.12

import gui 1.0

AdvancedDropArea {
    id: root
    property var label: "Drop to load file"
    property var icon: true
    Item {
        visible: parent.containsDrag
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            color: "black"
            opacity: 0.3
        }

        Glow {
            opacity: 0.3
            visible: dropText.visible
            anchors.fill: dropText
            radius: 4
            samples: 4
            color: "#000000"
            source: dropText
        }

        SText {
            id: dropText
            text: root.label
            visible: text != ""
            anchors.horizontalCenter: dropIcon.horizontalCenter
            anchors.bottom: dropIcon.top
            anchors.bottomMargin: 5
            color: COMMON.fg2
            pointSize: 10
            font.bold: true
        }

        Glow {
            visible: dropIcon.visible
            opacity: 0.3
            anchors.fill: dropIcon
            radius: 4
            samples: 4
            color: "#000000"
            source: dropIcon
        }

        Image {
            id: dropIcon
            visible: root.icon
            source: "qrc:/icons/download.svg"
            height: 30
            width: height
            sourceSize: Qt.size(width*1.25, height*1.25)
            anchors.centerIn: parent
        }

        ColorOverlay {
            id: dropIconOverlay
            visible: dropIcon.visible
            anchors.fill: dropIcon
            source: dropIcon
            color: COMMON.fg2
        }
    }
}