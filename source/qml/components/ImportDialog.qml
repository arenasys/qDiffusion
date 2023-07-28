import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

Dialog {
    id: dialog
    anchors.centerIn: parent
    width: raw ? Math.max(parent.width - 200, 400) : 400
    dim: true
    property alias parser: parser
    property var raw: false
    property var reset: true

    function tr(str, file = "ImportDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    height: paramList.contentHeight + 77

    padding: 5

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

    ParametersParser {
        id: parser

        onSuccess: {
            dialog.open()
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
            font.pointSize: 9
            font.bold: true
        }
        SIconButton {
            color: "transparent"
            icon: "qrc:/icons/eye.svg"
            tooltip: dialog.raw ? dialog.tr("Show parsed parameters") : dialog.tr("Show raw parameters")
            anchors.top: parent.top
            anchors.right: parent.right
            height: 20
            width: 20

            onPressed: {
                dialog.raw = !dialog.raw
            }
        }
    }

    contentItem: Rectangle {
        color: COMMON.bg00
        border.width: 1
        border.color: COMMON.bg5

        ListView {
            visible: !dialog.raw
            id: paramList
            model: parser.parameters
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 10
            height: contentHeight

            boundsBehavior: Flickable.StopAtBounds

            delegate: Item {
                width: parent.width
                height: (modelData.label == "Prompt" || modelData.label == "Negative prompt") ? 40 : 20
                property var checked: modelData.checked

                property var reset: modelData.name == "reset"

                onCheckedChanged: {
                    if(modelData.checked != checked) {
                        modelData.checked = checked
                    }
                }

                Rectangle {
                    id: check
                    anchors.left: parent.left
                    anchors.top: parent.top
                    height: 21
                    width: 21
                    border.color: reset ? COMMON.bg5 : COMMON.bg4
                    color: reset ? COMMON.bg3 : COMMON.bg2

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 3
                        border.color: reset ? COMMON.bg4 : COMMON.bg3
                        color: reset ? COMMON.bg2 : COMMON.bg1
                    }

                    Image {
                        id: img
                        width: 16
                        height: 16
                        visible:  modelData.checked
                        anchors.centerIn: parent
                        source: "qrc:/icons/tick.svg"
                        sourceSize: Qt.size(parent.width, parent.height)
                    }

                    ColorOverlay {
                        id: color
                        visible:  modelData.checked
                        anchors.fill: img
                        source: img
                        color: COMMON.fg1
                    }
                }

                Rectangle {
                    anchors.fill: label
                    border.color: reset ? COMMON.bg5 : COMMON.bg4
                    color: reset ? COMMON.bg4 : COMMON.bg3
                }

                SText {
                    id: label
                    anchors.top: parent.top
                    anchors.left: check.right
                    anchors.leftMargin: -1
                    height: 21
                    width: contentWidth+10
                    leftPadding: 5
                    rightPadding: 5
                    text: dialog.tr(modelData.label)
                    color: COMMON.fg1
                    opacity: 0.8
                    font.pointSize: 9.8
                }

                Rectangle {
                    visible: !reset
                    anchors.top: value.top
                    anchors.left: value.left
                    anchors.bottom: value.bottom
                    width: value.contentWidth+10
                    color: COMMON.bg1
                    border.color: COMMON.bg4
                }
                
                SText {
                    id: value
                    anchors.top: parent.height == 40 ? label.bottom : parent.top
                    anchors.left: parent.height == 40 ? parent.left : label.right
                    anchors.right: parent.right
                    anchors.topMargin: parent.height == 40 ? -1 : 0
                    anchors.leftMargin: parent.height == 40 ? 0 : -1
                    height: 21
                    leftPadding: 5
                    rightPadding: 5
                    text: modelData.value
                    elide: Text.ElideRight
                    color: COMMON.fg2
                    opacity: 0.8
                    font.pointSize: 9.8
                }                
            }
        }

        MouseArea {
            anchors.fill: paramList
            hoverEnabled: true
            property var mode: false
            property var lastItem: null

            onPressed: {
                if(mouseX > 20) {
                    return
                }
                lastItem = paramList.itemAt(mouseX, mouseY)
                if(lastItem != null) {
                    mode = !lastItem.checked
                    lastItem.checked = mode
                }
            }

            onPositionChanged: {
                if(!pressed || mouseX > 20) {
                    return
                }
                var item = paramList.itemAt(mouseX, mouseY)
                if(item != lastItem && item != null) {
                    lastItem = item
                    lastItem.checked = mode
                }
            }
        }


        STextArea {
            visible: dialog.raw
            anchors.fill: parent
            readOnly: true
            text: parser.formatted
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
                    font.pointSize: 9
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
}