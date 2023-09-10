import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"
import "../components"

Item {
    id: root
    width: parent.width

    property var source
    property var label
    property var model

    property alias type: choice_input.value
    property alias value: text_input.text
    property alias match: match_input.value

    property var mode: source.gridTypeMode(type)
    property var options: source.gridTypeOptions(type)

    property var valid: source.gridValidate(type, value)

    property alias target: text_input

    property var highlighter
    property alias menuActive: text_input.menuActive

    Row {
        anchors.fill: parent
        Item {
            width: 150
            height: root.height
            OChoice {
                id: choice_input
                width: parent.width
                height: 30
                rightPadding: false
                label: root.label
                model: root.model

                overlay: value == "None"
            }

            OTextInput {
                id: match_input
                anchors.top: choice_input.bottom
                anchors.topMargin: 2
                visible: choice_input.value == "Replace"
                width: parent.width + 2
                height: visible ? 30 : 0
                label: "Match"
                overlay: value == "None"
            }
        }

        Item {
            width: parent.width - 150
            height: root.height
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                anchors.leftMargin: 4
                color: COMMON.bg2_5
                border.color: COMMON.bg4
                STextArea {
                    id: text_input
                    anchors.fill: parent
                    overlay: choice_input.overlay

                    Component.onCompleted: {
                        root.highlighter = GUI.setHighlighting(area.textDocument)
                    }
                }

                Rectangle {
                    visible: !root.valid
                    anchors.fill: parent
                    color: "transparent"
                    border.color: COMMON.accent(0)
                    opacity: 0.4
                }
            }
        }
    }
}