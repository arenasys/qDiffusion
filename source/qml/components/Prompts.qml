import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    id: root
    clip: true

    property alias positivePrompt: promptPositive.text
    property alias negativePrompt: promptNegative.text

    property alias positivePromptArea: promptPositive
    property alias negativePromptArea: promptNegative

    property var active: promptPositive
    property var inactive: promptNegative

    property var cursorX: null
    property var cursorY: null
    property var cursorHeight: 0
    property var cursorText: null
    property var cursorPosition: null

    property variant bindMap: null

    function tr(str, file = "Prompts.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    signal inspect()
    signal tab()
    signal input(int key)
    signal release(int key)
    signal menu(int dir)

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
                    text: root.tr("Prompt")
                    color: COMMON.fg1_5
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: showButton.visible ? showButton.left : parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: root.tr("Inspect")
                    icon: "qrc:/icons/search.svg"
                    inset: 8
                    onPressed: {
                        root.inspect()
                    }
                }

                SIconButton {
                    id: showButton
                    visible: promptDivider.offset == 5
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: root.tr("Show Negative prompt")
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

                property var cursorX: promptPositive.area.cursorRectangle.x
                property var cursorY: promptPositive.area.cursorRectangle.y

                onInput: {
                    root.input(key)
                }

                onRelease: {
                    root.release(key)
                }

                onMenu: {
                    root.menu(dir)
                }

                area.onActiveFocusChanged: {
                    if(promptPositive.area.activeFocus) {
                        root.cursorX = Qt.binding(function () {return promptPositive.area.mapToItem(root, 0, 0).x + cursorX; })
                        root.cursorY = Qt.binding(function () {return promptPositive.area.mapToItem(root, 0, 0).y + cursorY; })
                        root.cursorText = Qt.binding(function () {return promptPositive.area.text; })
                        root.cursorPosition = Qt.binding(function () {return promptPositive.area.cursorPosition; })
                        root.cursorHeight = promptPositive.area.cursorRectangle.height
                        root.active = promptPositive
                        root.inactive = promptNegative
                    } else {
                        root.cursorX = null
                        root.cursorY = null
                        root.cursorText = null
                    }
                }

                onTab: {
                    root.tab()
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
                    text: root.tr("Negative Prompt")
                    color: COMMON.fg1_5
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
                    tooltip: root.tr("Hide Negative prompt")
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

                property var cursorX: promptNegative.area.cursorRectangle.x
                property var cursorY: promptNegative.area.cursorRectangle.y

                onInput: {
                    root.input(key)
                }

                onRelease: {
                    root.release(key)
                }

                onMenu: {
                    root.menu(dir)
                }

                area.onActiveFocusChanged: {
                    if(promptNegative.area.activeFocus) {
                        root.cursorX = Qt.binding(function () {return promptNegative.mapToItem(root, 0, 0).x + cursorX; })
                        root.cursorY = Qt.binding(function () {return promptNegative.mapToItem(root, 0, 0).y + cursorY; })
                        root.cursorText = Qt.binding(function () {return promptNegative.area.text; })
                        root.cursorPosition = Qt.binding(function () {return promptNegative.area.cursorPosition; })
                        root.cursorHeight = promptNegative.area.cursorRectangle.height
                        root.active = promptNegative
                        root.inactive = promptPositive
                    } else {
                        root.cursorX = null
                        root.cursorY = null
                        root.cursorText = null
                    }
                }

                onTab: {
                    root.tab()
                }
            }
        }
    }
}