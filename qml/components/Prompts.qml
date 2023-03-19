import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    id: root
    clip: true

    property alias positivePrompt: promptPositive.text
    property alias negativePrompt: promptNegative.text

    Item {
        width: Math.max(260, parent.width)
        height: Math.max(100, parent.height)
        Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: areaNegative.left
            anchors.margins: 5
            border.width: 1
            border.color: COMMON.bg4
            color: "transparent"

            Rectangle {
                id: headerPositive
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 25
                border.width: 1
                border.color: COMMON.bg4
                color: COMMON.bg3
                SText {
                    anchors.fill: parent
                    text: "Prompt"
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    visible: !areaNegative.show
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: "Show Negative prompt"
                    icon: "qrc:/icons/eye.svg"
                    onPressed: {
                        areaNegative.show = true
                    }
                }
            }

            STextArea {
                id: promptPositive
                color: COMMON.bg1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: headerPositive.bottom
                anchors.bottom: parent.bottom
                anchors.margins: 1
            }
        }

        Rectangle {
            clip: true
            property bool show: true
            id: areaNegative
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: show ? parent.width/2 - 5 : 0
            anchors.margins: show ? 5 : 0
            border.width: 1
            border.color: COMMON.bg4
            color: "transparent"

            Rectangle {
                id: headerNegative
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 25
                border.width: 1
                border.color: COMMON.bg4
                color: COMMON.bg3
                SText {
                    anchors.fill: parent
                    text: "Negative Prompt"
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: "Hide Negative prompt"
                    icon: "qrc:/icons/eye.svg"

                    onPressed: {
                        areaNegative.show = false
                    }
                }
            }

            STextArea {
                id: promptNegative
                color: COMMON.bg1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: headerNegative.bottom
                anchors.bottom: parent.bottom
                anchors.margins: 1
            }
        }
    }
}