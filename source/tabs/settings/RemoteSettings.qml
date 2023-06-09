import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root

    property var show: GUI.remoteStatus == 2

    Column {
        anchors.centerIn: parent
        height: parent.height-100
        width: parent.width/2

        Item {
            width: parent.width
            height: 30
            OTextInput {
                id: endpointInput
                anchors.left: parent.left
                anchors.right: disconnectButton.visible ? disconnectButton.left : parent.right
                height: 30
                label: "Endpoint"
                placeholder: "Local"

                bindMap: GUI.config
                bindKey: "endpoint"
            }

            SIconButton {
                id: disconnectButton
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: 2
                anchors.rightMargin: 2
                visible: endpointInput.value != "" && GUI.remoteStatus != 0
                height: 28
                width: visible ? 28 : 0
                anchors.margins: 0
                tooltip: "Disconnect"
                icon: "qrc:/icons/disconnect.svg"
                border.color: COMMON.bg4

                onPressed: {
                    endpointInput.value = ""
                    passwordInput.value = ""
                    SETTINGS.restart()
                }
            }
        }

        OTextInput {
            id: passwordInput
            width: parent.width
            height: 30
            label: "Password"
            placeholder: "None"
            bindMap: GUI.config
            bindKey: "password"
        }

        SButton {
            width: parent.width
            height: 30
            label: endpointInput.value == "" ? "Reload" : "Reconnect"
            onPressed: {
                SETTINGS.restart()
            }
        }

        SText {
            text: GUI.remoteInfo
            width: parent.width
            height: 30
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 9.8
            color: COMMON.fg2
        }

        Item {
            width: parent.width
            height: 30
        }

        Item {
            width: parent.width
            height: 30
            OChoice {
                anchors.left: parent.left
                anchors.top: parent.top
                id: modelTypeInput
                width: 120
                height: 30
                label: "Type"
                model: ["SD", "LoRA", "HN", "TI", "SR", "CN"]
                disabled: !root.show
            }
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: modelTypeInput.right
                anchors.right: parent.right
                anchors.top: parent.top
                id: modelUrlInput
                height: 30
                label: ""
                placeholder: "URL"
                disabled: !root.show
            }
        }
        SButton {
            width: parent.width
            height: 30
            label: "Download"
            onPressed: {
                SETTINGS.download(modelTypeInput.model[modelTypeInput.currentIndex], modelUrlInput.value)
            }
            disabled: !root.show
        }

        Item {
            width: parent.width
            height: 30
        }


        Item {
            width: parent.width
            height: 30
            OChoice {
                anchors.left: parent.left
                anchors.top: parent.top
                id: uploadTypeInput
                width: 120
                height: 30
                label: "Type"
                model: ["SD", "LoRA", "HN", "TI", "SR", "CN"]
                disabled: !root.show
            }
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: uploadTypeInput.right
                anchors.right: uploadFileButton.left
                anchors.top: parent.top
                id: uploadFileInput
                height: 30
                label: ""
                placeholder: "File"
                disabled: !root.show
            }

            Connections {
                target: SETTINGS
                function onCurrentUploadChanged() {
                    uploadFileInput.value = SETTINGS.currentUpload
                }

                function onCurrentUploadModeChanged() {
                    uploadTypeInput.currentIndex = SETTINGS.currentUploadMode
                }
            }

            SIconButton {
                id: uploadFileButton
                height: 28
                width: 28
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 2
                tooltip: "Select file"
                icon: "qrc:/icons/folder.svg"
                border.color: COMMON.bg4

                onPressed: {
                    uploadFileDialog.open()
                }
                disabled: !root.show
            }

            FileDialog {
                id: uploadFileDialog
                nameFilters: ["Model files (*.ckpt *.safetensors *.pt *.pth)"]

                onAccepted: {
                    uploadFileInput.value = SETTINGS.toLocal(uploadFileDialog.file)
                }
            }

            AdvancedDropArea {
                id: uploadFileDrop
                anchors.fill: uploadFileInput

                onDropped: {
                    var file = SETTINGS.pathDrop(mimeData)
                    if(file != null) {
                        uploadFileInput.value = file
                    }
                }

                Rectangle {
                    visible: uploadFileDrop.containsDrag
                    anchors.fill: parent
                    color: "transparent"
                    border.color: COMMON.fg2
                    anchors.topMargin: 2
                    anchors.leftMargin: 2
                    anchors.rightMargin: 2
                    
                }
            }
        }

        SButton {
            width: parent.width
            height: 30
            label: "Upload"
            onPressed: {
                SETTINGS.upload(uploadTypeInput.model[uploadTypeInput.currentIndex], uploadFileInput.value)
            }
            disabled: !root.show
        }

        Item {
            width: parent.width
            height: 30
        }

        STextArea {
            id: logTextArea
            width: parent.width
            height: 100
            text: SETTINGS.log
            readOnly: true
            area.color: COMMON.fg1
            

            onTextChanged: {
                area.cursorPosition = text.length-1
            }

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: COMMON.bg4
            }

            Rectangle {
                anchors.fill: parent
                visible: !root.show
                color: "#80101010"
            }
        }
    }

    Rectangle {
        visible: false
        anchors.fill: parent
        color: "#101010"
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        }

        SText {
            anchors.fill: parent
            font.pointSize: 20
            font.bold: true
            color: COMMON.fg1
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: "Not ready"
        }
    }
}