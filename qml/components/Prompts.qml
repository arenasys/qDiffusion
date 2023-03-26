import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    id: root
    clip: true

    property alias positivePrompt: promptPositive.text
    property alias negativePrompt: promptNegative.text

    property variant bindMap: null

    Connections {
        target: bindMap
        function onUpdated() {
            var p = root.bindMap.get("prompt")
            if(p != root.positivePrompt) {
                root.positivePrompt = p
            }
            var n = root.bindMap.get("negative_prompt")
            if(n != root.negativePrompt) {
                root.negativePrompt = n
            }
        }
    }

    Component.onCompleted: {
        if(root.bindMap != null) {
            root.positivePrompt = root.bindMap.get("prompt")
            root.negativePrompt = root.bindMap.get("negative_prompt")
        }
    }

    onPositivePromptChanged: {
        if(root.bindMap != null) {
            root.bindMap.set("prompt", root.positivePrompt)
        }
    }

    onNegativePromptChanged: {
        if(root.bindMap != null) {
            root.bindMap.set("negative_prompt", root.negativePrompt)
        }
    }

    Item {
        id: area
        width: Math.max(260, parent.width)
        height: Math.max(100, parent.height)
        Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Math.max(200, promptDivider.x - 5)
            anchors.right: promptDivider.left
            anchors.margins: 5
            anchors.rightMargin: 0
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
                    visible: promptDivider.offset == 5
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: "Show Negative prompt"
                    icon: "qrc:/icons/eye.svg"
                    onPressed: {
                        promptDivider.offset = area.width/2
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

                onTab: {
                    promptNegative.forceActiveFocus()
                }
            }
        }

        SDividerVR {
            id: promptDivider
            color: "transparent"
            offset: parent.width/2
            minOffset: 5
            maxOffset: parent.width
            snap: parent.width/2
        }

        Rectangle {
            clip: true
            id: areaNegative
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: promptDivider.right
            width: Math.max(200, parent.width - promptDivider.x - 10)
            anchors.margins: 5
            anchors.leftMargin: 0
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
                        promptDivider.offset = 5
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

                onTab: {
                    promptPositive.forceActiveFocus()
                }
            }
        }
    }
}