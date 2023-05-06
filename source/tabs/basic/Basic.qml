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
    property var swap: GUI.config.get("swap")

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
            value: GUI.modelName(BASIC.parameters.values.get("UNET")) + ".safetensors"
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

    Item {
        id: leftArea
        anchors.left: parent.left
        anchors.right: divider.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }

    SDividerVR {
        id: rightDivider
        visible: !root.swap
        minOffset: 5
        maxOffset: 300
        offset: 210
    }

    SDividerVL {
        id: leftDivider
        visible: root.swap
        minOffset: 0
        maxOffset: 300
        offset: 210
    }
    
    Item {
        id: rightArea
        anchors.left: divider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }

    property var divider: root.swap ? leftDivider : rightDivider
    property var mainArea: root.swap ? rightArea : leftArea
    property var settingsArea: root.swap ? leftArea : rightArea

    BasicAreas {
        id: areas
        anchors.left: mainArea.left
        anchors.top: mainArea.top
        anchors.right: mainArea.right
        anchors.bottom: promptDivider.top
    }

    BasicFull {
        id: full
        anchors.fill: areas

        onContextMenu: {
            if(BASIC.openedArea == "output" && full.target.ready) {
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

            property var output: full.target != null && full.target.file != ""

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

    Rectangle {
        id: settings
        color: COMMON.bg0
        anchors.left: settingsArea.left
        anchors.right: settingsArea.right
        anchors.top: settingsArea.top
        anchors.bottom: statusDivider.top

        Parameters {
            id: params
            anchors.fill: parent
            binding: BASIC.parameters
            swap: root.swap

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
        anchors.left: settingsArea.left
        anchors.right: settingsArea.right
        minOffset: 50
        maxOffset: 70
        offset: 50
    }

    Status {
        anchors.top: statusDivider.bottom
        anchors.bottom: settingsArea.bottom
        anchors.left: settingsArea.left
        anchors.right: settingsArea.right
    }

    SDividerHB {
        id: promptDivider
        anchors.left: mainArea.left
        anchors.right: mainArea.right
        minOffset: 5
        maxOffset: 300
        offset: 150
    }

    Prompts {
        id: prompts
        anchors.left: mainArea.left
        anchors.right: mainArea.right
        anchors.bottom: mainArea.bottom
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