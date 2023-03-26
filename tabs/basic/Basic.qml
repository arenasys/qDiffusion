import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.0


import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    clip: true

    function releaseFocus() {
        parent.releaseFocus()
    }

    AdvancedDropArea {
        id: basicDrop
        anchors.fill: parent

        onDropped: {
            BASIC.pasteDrop(mimeData)
        }
    }

    BasicAreas {
        id: areas
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.right: settingsDivider.left
        anchors.bottom: promptDivider.top
    }

    BasicFull {
        id: full
        anchors.fill: areas
    }


    SDividerVR {
        id: settingsDivider
        minOffset: 5
        maxOffset: 300
        offset: 210
    }

    Rectangle {
        id: settings
        color: COMMON.bg1
        anchors.left: settingsDivider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: statusDivider.top

        Parameters {
            id: params
            anchors.fill: parent
            binding: BASIC.parameters

            onGenerate: {
                BASIC.generate()
            }
            onCancel: {
                BASIC.cancel()
            }
            onForeverChanged: {
                BASIC.forever = params.forever
            }
        }
    }

    SDividerHB {
        id: statusDivider
        anchors.left: settings.left
        anchors.right: parent.right
        minOffset: 50
        maxOffset: 100
        offset: 50
    }

    Status {
        anchors.top: statusDivider.bottom
        anchors.bottom: parent.bottom
        anchors.left: statusDivider.left
        anchors.right: parent.right
    }

    SDividerHB {
        id: promptDivider
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        minOffset: 5
        maxOffset: 300
        offset: 150
    }

    Prompts {
        id: prompts
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        anchors.bottom: parent.bottom
        anchors.top: promptDivider.bottom

        bindMap: BASIC.parameters.values

        onPositivePromptChanged: {
            BASIC.parameters.promptsChanged()
        }
        onNegativePromptChanged: {
            BASIC.parameters.promptsChanged()
        }

    }

    Rectangle {
        id: fullParams
        anchors.fill: prompts
        visible: full.visible && parameters != "" && show
        color: COMMON.bg0
        property var parameters: full.target != null ? (full.target.parameters != undefined ? full.target.parameters : "") : ""
        property var show: true

        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            border.width: 1
            border.color: COMMON.bg4
            color: "transparent"

            Rectangle {
                id: headerParams
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 25
                border.width: 1
                border.color: COMMON.bg4
                color: COMMON.bg3
                SText {
                    anchors.fill: parent
                    text: "Parameters"
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    visible: fullParams.visible
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: "Hide Parameters"
                    icon: "qrc:/icons/eye.svg"
                    onPressed: {
                        fullParams.show = false
                    }
                }
            }

            STextArea {
                color: COMMON.bg1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: headerParams.bottom
                anchors.bottom: parent.bottom
                anchors.margins: 1

                readOnly: true

                text: fullParams.parameters
            }
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_V:
                BASIC.pasteClipboard()
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            default:
                event.accepted = false
                break;
            }
        }
    }

    ImportDialog  {
        id: importDialog
        title: "Import"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        dim: true

        onAccepted: {
            BASIC.parameters.sync(importDialog.parser.parameters)
        }

        onClosed: {
            importDialog.parser.formatted = ""
        }

        Connections {
            target: BASIC
            function onPastedText(text) {
                importDialog.parser.formatted = text
            }
        }
    }

    Keys.forwardTo: [areas, full]
}