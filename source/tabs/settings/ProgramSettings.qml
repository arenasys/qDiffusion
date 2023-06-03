import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

Item {
    Column {
        anchors.centerIn: parent
        height: parent.height-100
        width: parent.width/2

        SButton {
            width: parent.width
            height: 30
            label: "Update"
            onPressed: {
                SETTINGS.update()
            }
        }
        STextSelectable {
            text: SETTINGS.gitInfo
            width: parent.width
            height: 30
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 9.8
            color: COMMON.fg2
        }
        STextSelectable {
            text: SETTINGS.gitServerInfo
            width: parent.width
            height: text != "" ? 10 : 0
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 9.8
            color: COMMON.fg2
        }
        
        Item {
            width: parent.width
            height: SETTINGS.updating ? 50 : 30
            LoadingSpinner {
                size: 20
                running: SETTINGS.updating
                anchors.fill: parent
            }
            SText {
                text: "Restart required"
                visible: !SETTINGS.updating && SETTINGS.needRestart
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9.0
                color: COMMON.accent(0)
            }
        }

        Item {
            width: parent.width
            height: SETTINGS.updating ? 10 : 30
        }

        Item {
            width: parent.width
            height: 30
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: parent.left
                anchors.right: setOutputButton.left
                anchors.top: parent.top
                id: outputFolderInput
                height: 30
                label: "Output Folder"
                placeholder: "outputs"
                value: GUI.config.get("output_directory")

                onValueChanged: {
                    GUI.config.set("output_directory", value)
                }
            }

            SIconButton {
                id: setOutputButton
                height: 28
                width: 28
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 2
                icon: "qrc:/icons/folder.svg"
                border.color: COMMON.bg4

                onPressed: {
                    outputFolderDialog.open()
                }
            }

            FolderDialog {
                id: outputFolderDialog

                onAccepted: {
                    outputFolderInput.value = SETTINGS.toLocal(outputFolderDialog.folder)
                }
            }

            AdvancedDropArea {
                id: outputFolderDrop
                anchors.fill: outputFolderInput

                onDropped: {
                    var folder = SETTINGS.pathDrop(mimeData)
                    if(folder != null) {
                        outputFolderInput.value = folder
                    }
                }

                Rectangle {
                    visible: outputFolderDrop.containsDrag
                    anchors.fill: parent
                    color: "transparent"
                    border.color: COMMON.fg2
                    anchors.topMargin: 2
                    anchors.leftMargin: 2
                    anchors.rightMargin: 2
                }
            }
        }

        Item {
            width: parent.width
            height: 30
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: parent.left
                anchors.right: setmodelButton.left
                anchors.top: parent.top
                id: modelFolderInput
                height: 30
                label: "Model Folder"
                placeholder: "models"

                value: GUI.config.get("model_directory")

                onValueChanged: {
                    GUI.config.set("model_directory", value)
                }
            }

            SIconButton {
                id: setmodelButton
                height: 28
                width: 28
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 2
                icon: "qrc:/icons/folder.svg"
                border.color: COMMON.bg4

                onPressed: {
                    modelFolderDialog.open()
                }
            }

            FolderDialog {
                id: modelFolderDialog

                onAccepted: {
                    modelFolderInput.value = SETTINGS.toLocal(modelFolderDialog.folder)
                }
            }

            AdvancedDropArea {
                id: modelFolderDrop
                anchors.fill: modelFolderInput

                onDropped: {
                    var folder = SETTINGS.pathDrop(mimeData)
                    if(folder != null) {
                        modelFolderInput.value = folder
                    }
                }

                Rectangle {
                    visible: modelFolderDrop.containsDrag
                    anchors.fill: parent
                    color: "transparent"
                    border.color: COMMON.fg2
                    anchors.topMargin: 2
                    anchors.leftMargin: 2
                    anchors.rightMargin: 2
                }
            }
        }
        OChoice {
            x: -2
            width: parent.width+2
            height: 30
            label: "Debug Logging"
            currentIndex: GUI.config.get("debug") ? 1 : 0 
            model: ["Disabled", "Enabled"]
            onCurrentIndexChanged: {
                GUI.config.set("debug", currentIndex != 0)
            }
        }
        OChoice {
            x: -2
            width: parent.width+2
            height: 30
            label: "Advanced Parameters"
            currentIndex: GUI.config.get("advanced") ? 1 : 0 
            model: ["Hide", "Show"]
            onCurrentIndexChanged: {
                GUI.config.set("advanced", currentIndex != 0)
            }
        }
    }
}