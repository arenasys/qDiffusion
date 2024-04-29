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

    contentItem: Rectangle {
        id: content
        color: COMMON.bg0
        border.width: 1
        border.color: COMMON.bg5
        anchors.fill: parent

        Column {
            anchors.fill: parent
            anchors.leftMargin: 5
            anchors.rightMargin: 5

            Item {
                width: parent.width
                height: 3
            }

            Item {
                width: parent.width
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
            }

            Item {
                width: parent.width
                height: 0
            }

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
    }
}