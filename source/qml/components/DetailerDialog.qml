import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"


SMovableDialog {
    id: dialog
    
    property var detailer
    property var settings: BASIC.detailers.settings(detailer)
    property var suggestions: BASIC.detailers.suggestions

    Component.onCompleted: {
        dialog.setAnchored(true)
        dialog.open()
    }

    function doSave() {
        BASIC.detailers.saveSettings(detailer)
    }

    function doFinish() {
        BASIC.detailers.closeSettings(detailer)
        dialog.destroy()
    }

    onAccepted: {
        doFinish()
    }
    
    onRejected: {
        doFinish()
    }

    Connections {
        target: BASIC.detailers
        function onClosingSettings(detailer) {
            if(detailer === dialog.detailer) {
                dialog.doFinish()
            }
        }
    }

    Timer {
        id: saveTimer
        interval: 500
        running: false
        onTriggered: {
            dialog.doSave()
        }
    }

    function save() {
        saveTimer.restart()
    }

    title: dialog.tr("Detailer")
    minWidth: 220
    minHeight: 257
    standardButtons: dialog.anchored ? Dialog.Ok : 0

    function tr(str, file = "DetailerDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    property var showingPrompt: dialog.width > 340 

    contentItem: Rectangle {
        id: content
        color: COMMON.bg0
        border.width: 1
        border.color: COMMON.bg5
        anchors.fill: parent

        Item {
            id: header
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            anchors.topMargin: 3
            height: 20
            
            Rectangle {
                anchors.centerIn: parent
                width: nameText.width + 10
                height: parent.height
                color: COMMON.bg2
                border.width: 1
                border.color: COMMON.bg4
            }

            SText {
                id: nameText
                text: GUI.modelName(dialog.detailer)
                anchors.centerIn: parent
                pointSize: 9.8
                color: COMMON.fg1_5
            }

            SIconButton {
                visible: !dialog.showingPrompt
                id: promptButton
                color: COMMON.bg2
                border.width: 1
                border.color: COMMON.bg4
                icon: "qrc:/icons/text_2.svg"
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.rightMargin: 2
                height: 20
                width: visible ? 20 : 0
                inset: 6
                onPressed: {
                    dialog.usualWidth = 550
                }
            }
        }

        Column {
            id: column
            anchors.top: header.bottom
            anchors.left: parent.left
            anchors.leftMargin: 5
            width: showingPrompt ? 200 : content.width - 10
            height: 236

            OSlider {
                id: resInput
                label: dialog.tr("Resolution")
                width: parent.width
                height: 30

                bindMap: dialog.settings
                bindKey: "resolution"

                minValue: 64
                maxValue: 1024
                precValue: 0
                incValue: 8
                snapValue: 64
                bounded: false

                onValueChanged: {
                    dialog.save()
                }
            }

            OSlider {
                id: strengthInput
                label: dialog.tr("Strength")
                width: parent.width
                height: 30
                
                bindMap: dialog.settings
                bindKey: "strength"

                minValue: 0
                maxValue: 1
                precValue: 2
                incValue: 0.01
                snapValue: 0.05

                onValueChanged: {
                    dialog.save()
                }
            }

            OSlider {
                id: paddingInput
                label: dialog.tr("Padding")
                width: parent.width
                height: 30

                bindMap: dialog.settings
                bindKey: "padding"

                minValue: 0
                maxValue: 512
                precValue: 0
                incValue: 8
                snapValue: 16
                bounded: false

                onValueChanged: {
                    dialog.save()
                }
            }

            OSlider {
                label: dialog.tr("Mask Blur")
                width: parent.width
                height: 30

                bindMap: dialog.settings
                bindKey: "mask_blur"

                minValue: 0
                maxValue: 10
                precValue: 0
                incValue: 1
                snapValue: 1
                bounded: false

                onValueChanged: {
                    dialog.save()
                }
            }

            OSlider {
                label: dialog.tr("Mask Expand")
                width: parent.width
                height: 30

                bindMap: dialog.settings
                bindKey: "mask_expand"

                minValue: 0
                maxValue: 10
                precValue: 0
                incValue: 1
                snapValue: 1
                bounded: false

                onValueChanged: {
                    dialog.save()
                }
            }


            OSlider {
                id: thresholdInput
                label: dialog.tr("Threshold")
                width: parent.width
                height: 30
                
                bindMap: dialog.settings
                bindKey: "threshold"

                minValue: 0
                maxValue: 1
                precValue: 2
                incValue: 0.01
                snapValue: 0.05

                onValueChanged: {
                    dialog.save()
                }
            }
            
            OChoice {
                id: modeInput
                label: dialog.tr("Box mode")
                width: parent.width
                height: 30
                
                bindMap: dialog.settings
                bindKeyCurrent: "box_mode"
                bindKeyModel: "box_modes"
                
                popupHeight: dialog.height + 100

                onValueChanged: {
                    dialog.save()
                }
            }
        }

        Item {
            visible: dialog.showingPrompt
            anchors.top: header.bottom
            anchors.bottom: parent.bottom
            anchors.left: column.right
            anchors.right: parent.right
            anchors.margins: 3
            anchors.leftMargin: 1
            anchors.topMargin: 1
            clip: true

            Rectangle {
                anchors.fill: parent
                border.width: 1
                border.color: COMMON.bg4
                color: "transparent"
                anchors.margins: 1

                Rectangle {
                    id: promptHeader
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 20
                    border.width: 1
                    border.color: COMMON.bg4
                    color: COMMON.bg3
                    SText {
                        anchors.fill: parent
                        text: root.tr("Detailer Prompt")
                        pointSize: 9.8
                        color: COMMON.fg1_5
                        leftPadding: 5
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                STextArea {
                    id: promptDetailer
                    color: COMMON.bg1
                    anchors.top: promptHeader.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 1
                    menuActive: suggestions.active

                    Component.onCompleted: {
                        promptDetailer.text = dialog.settings.get("prompt")
                        GUI.setHighlighting(promptDetailer.area.textDocument)
                    }

                    onTextChanged: {
                        dialog.settings.set("prompt", promptDetailer.text)
                        dialog.save()
                    }
                }
            }
        }

        Suggestions {
            id: suggestions
            target: promptDetailer
            suggestions: dialog.suggestions
            x: promptDetailer.mapToItem(content, 0, 0).x + area.cursorRectangle.x;
            y: promptDetailer.mapToItem(content, 0, 0).y + area.cursorRectangle.y;
            height: area.cursorRectangle.height
            visible: area.activeFocus

            Component.onCompleted: {
                dialog.suggestions.setPromptSources()
            }
        }
    }
}