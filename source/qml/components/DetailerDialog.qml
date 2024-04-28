import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

Dialog {
    id: dialog
    anchors.centerIn: parent
    title: root.tr("Detailer")
    width: 220
    dim: true
    height: 292
    padding: 5
    closePolicy: Popup.NoAutoClose

    function tr(str, file = "DetailerDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    onOpened: {
        enterItem.forceActiveFocus()
    }

    Item {
        id: enterItem
        Keys.onPressed: {
            event.accepted = true
            switch(event.key) {
            case Qt.Key_Enter:
            case Qt.Key_Return:
                dialog.accept()
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }

    background: Item {
        RectangularGlow {
            anchors.fill: bg
            glowRadius: 5
            opacity: 0.75
            spread: 0.2
            color: "black"
            cornerRadius: 10
        }

        Rectangle {
            id: bg
            anchors.fill: parent
            anchors.margins: -1
            color: COMMON.bg1
            border.width: 1
            border.color: COMMON.bg4
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg0
        }
    }

    header: Item {
        implicitHeight: 20
        SText {
            color: COMMON.fg2
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: dialog.title
            pointSize: 9
            font.bold: true
        }
    }

    spacing: 0
    verticalPadding: 0

    footer: Rectangle {
        implicitWidth: parent.width
        implicitHeight: 35
        color: COMMON.bg1
        DialogButtonBox {
            anchors.centerIn: parent
            standardButtons: dialog.standardButtons
            alignment: Qt.AlignHCenter
            spacing: 5

            background: Item {
                implicitHeight: 25
            }

            delegate: Button {
                id: control
                implicitHeight: 25

                contentItem: SText {
                    id: contentText
                    color: COMMON.fg1
                    text: control.text
                    pointSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 0
                    color: control.down ? COMMON.bg5 : COMMON.bg4
                    border.color: COMMON.bg6
                }
            }

            onAccepted: dialog.accept()
            onRejected: dialog.reject()
        }
    }

    contentItem: Rectangle {
        id: content
        color: COMMON.bg0
        border.width: 1
        border.color: COMMON.bg5

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
                    text: BASIC.detailers.currentName
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
                label: root.tr("Resolution")
                width: parent.width
                height: 30

                bindMap: BASIC.detailers.values
                bindKey: "resolution"

                minValue: 64
                maxValue: 1024
                precValue: 0
                incValue: 8
                snapValue: 64
                bounded: false
            }

            OSlider {
                id: strengthInput
                label: root.tr("Strength")
                width: parent.width
                height: 30
                
                bindMap: BASIC.detailers.values
                bindKey: "strength"

                minValue: 0
                maxValue: 1
                precValue: 2
                incValue: 0.01
                snapValue: 0.05
            }

            OSlider {
                id: paddingInput
                label: root.tr("Padding")
                width: parent.width
                height: 30

                bindMap: BASIC.detailers.values
                bindKey: "padding"

                minValue: 0
                maxValue: 512
                precValue: 0
                incValue: 8
                snapValue: 16
                bounded: false
            }

            OSlider {
                label: root.tr("Mask Blur")
                width: parent.width
                height: 30

                bindMap: BASIC.detailers.values
                bindKey: "mask_blur"

                minValue: 0
                maxValue: 10
                precValue: 0
                incValue: 1
                snapValue: 1
                bounded: false
            }

            OSlider {
                label: root.tr("Mask Expand")
                width: parent.width
                height: 30

                bindMap: BASIC.detailers.values
                bindKey: "mask_expand"

                minValue: 0
                maxValue: 10
                precValue: 0
                incValue: 1
                snapValue: 1
                bounded: false
            }


            OSlider {
                id: thresholdInput
                label: root.tr("Threshold")
                width: parent.width
                height: 30
                
                bindMap: BASIC.detailers.values
                bindKey: "threshold"

                minValue: 0
                maxValue: 1
                precValue: 2
                incValue: 0.01
                snapValue: 0.05
            }
            
            OChoice {
                id: modeInput
                label: root.tr("Box mode")
                width: parent.width
                height: 30
                
                bindMap: BASIC.detailers.values
                bindKeyCurrent: "box_mode"
                bindKeyModel: "box_modes"
                
                popupHeight: root.height + 100
            }
        }
    }
}