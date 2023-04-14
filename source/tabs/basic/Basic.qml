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

    SDialog {
        id: buildDialog
        title: "Build model"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        dim: true

        OTextInput {
            id: filenameInput
            width: 290
            height: 30
            label: "Filename"
            value: BASIC.parameters.values.get("UNET") + ".st"
        }

        width: 300
        height: 87

        onAccepted: {
            BASIC.buildModel(filenameInput.value)
        }
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

        onContextMenu: {
            if(BASIC.openedArea == "output") {
                fullContextMenu.popup()
            }
        }

        SContextMenu {
            id: fullContextMenu

            SContextMenuItem {
                text: "Show Parameters"
                checkable: true
                checked: fullParams.show
                onCheckedChanged: {
                    if(checked != fullParams.show) {
                        fullParams.show = checked
                        checked = Qt.binding(function() { return fullParams.show })
                    }
                }
            }

            property var output: full.file != ""

            SContextMenuSeparator {
                visible: fullContextMenu.output
            }

            SContextMenuItem {
                id: outputContext
                visible: fullContextMenu.output
                text: "Open"
                onTriggered: {
                    GALLERY.doOpenImage([full.file])
                }
            }

            SContextMenuItem {
                text: "Visit"
                visible: fullContextMenu.output
                onTriggered: {
                    GALLERY.doOpenFolder([full.file])
                }
            }

            SContextMenuSeparator {
                visible: fullContextMenu.output
            }

            Sql {
                id: destinationsSql
                query: "SELECT name, folder FROM folders WHERE UPPER(name) != UPPER('" + full.file + "');"
            }

            SContextMenu {
                id: fullCopyToMenu
                title: "Copy to"
                Instantiator {
                    model: destinationsSql
                    SContextMenuItem {
                        visible: fullContextMenu.output
                        text: sql_name
                        onTriggered: {
                            GALLERY.doCopy(sql_folder, [full.file])
                        }
                    }
                    onObjectAdded: fullCopyToMenu.insertItem(index, object)
                    onObjectRemoved: fullCopyToMenu.removeItem(object)
                }
            }
        }
    }

    SDividerVR {
        id: settingsDivider
        minOffset: 5
        maxOffset: 300
        offset: 210
    }

    Rectangle {
        id: settings
        color: COMMON.bg0
        anchors.left: settingsDivider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: statusDivider.top

        Parameters {
            id: params
            anchors.fill: parent
            binding: BASIC.parameters

            remaining: BASIC.remaining

            onGenerate: {
                BASIC.generate()
            }
            onCancel: {
                BASIC.cancel()
            }
            onForeverChanged: {
                BASIC.forever = params.forever
            }
            onBuildModel: {
                buildDialog.open()
            }
            function sizeDrop(mimeData) {
                BASIC.sizeDrop(mimeData)
            }
            function seedDrop(mimeData) {
                BASIC.seedDrop(mimeData)
            }
        }
    }

    SDividerHB {
        id: statusDivider
        anchors.left: settings.left
        anchors.right: parent.right
        minOffset: 50
        maxOffset: 70
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

        Component.onCompleted: {
            GUI.setHighlighting(positivePromptArea.area.textDocument)
            GUI.setHighlighting(negativePromptArea.area.textDocument)
        }

        onPositivePromptChanged: {
            BASIC.parameters.promptsChanged()
        }
        onNegativePromptChanged: {
            BASIC.parameters.promptsChanged()
        }
        onInspect: {
            BASIC.pasteText(positivePrompt)
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
                    color: COMMON.fg1_5
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

                Component.onCompleted: {
                    GUI.setHighlighting(area.textDocument)
                }
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