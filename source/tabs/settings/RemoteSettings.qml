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

    function tr(str, file = "RemoteSettings.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    function map(type) {
        return {"Checkpoint":"SD", "LoRA":"LoRA", "Embedding":"TI", "Upscaler":"SR"}[type]
    }

    property var show: GUI.isRemote && GUI.remoteStatus == 2

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
                label: root.tr("Endpoint")
                placeholder: root.tr("Local")

                bindMap: GUI.config
                bindKey: "endpoint"
            }

            SIconButton {
                id: disconnectButton
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: 2
                anchors.rightMargin: 2
                visible: endpointInput.value != "" && GUI.isRemote && GUI.remoteStatus != 0
                height: 28
                width: visible ? 28 : 0
                anchors.margins: 0
                tooltip: root.tr("Disconnect")
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
            label: root.tr("Password")
            placeholder: root.tr("None")
            bindMap: GUI.config
            bindKey: "password"
        }

        SButton {
            width: parent.width
            height: 30
            label: endpointInput.value == "" ? root.tr("Reload") : (GUI.remoteInfoMode == "Remote" ? root.tr("Reconnect") : root.tr("Connect"))
            onPressed: {
                SETTINGS.restart()
            }
        }

        SText {
            text: root.tr(GUI.remoteInfoMode, "Status") + ", " + root.tr(GUI.remoteInfoStatus, "Status")
            width: parent.width
            height: 30
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            pointSize: 9.8
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
                width: 140
                height: 30
                label: root.tr("Type")
                entries: ["Checkpoint", "LoRA", "Embedding", "Upscaler"]//["SD", "LoRA", "TI", "SR"]
                disabled: !root.show
            }
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: modelTypeInput.right
                anchors.right: keysButton.left
                anchors.top: parent.top
                id: modelUrlInput
                height: 30
                label: ""
                placeholder: "URL"
                disabled: !root.show
            }
            SIconButton {
                id: keysButton
                anchors.top: parent.top
                anchors.topMargin: 2
                anchors.right: parent.right
                anchors.rightMargin: 2
                width: height
                height: parent.height-2
                inset: 5
                icon: "qrc:/icons/key.svg"
                tooltip: root.tr(toggled ? "Hide API Keys" : "Show API Keys")
                border.color: COMMON.bg4
                border.width: 1

                iconHoverColor: toggled ? COMMON.fg0 : COMMON.fg3

                disabled: !root.show

                property var toggled: false
                onPressed: {
                    toggled = !toggled
                }
            }
        }

        Item {
            visible: keysButton.toggled
            width: parent.width
            height: visible ? 30 : 0
            OTextInput {
                anchors.fill: parent
                id: hfKeyInput
                label: "Huggingface API Key"
                placeholder: "None"
                Component.onCompleted: {
                    var token = GUI.config.get("hf_token")
                    value = token ? token : ""
                }
                onValueChanged: {
                    GUI.config.set("hf_token", value)
                }
            }
        }

        Item {
            visible: keysButton.toggled
            width: parent.width
            height: visible ? 30 : 0
            OTextInput {
                anchors.fill: parent
                id: civitaiKeyInput
                label: "CivitAI API Key"
                placeholder: "None"
                Component.onCompleted: {
                    var token = GUI.config.get("civitai_token")
                    value = token ? token : ""
                }
                onValueChanged: {
                    GUI.config.set("civitai_token", value)
                }
            }
        }


        SButton {
            width: parent.width
            height: 30
            label: root.tr("Download")
            onPressed: {
                var type = modelTypeInput.model[modelTypeInput.currentIndex]
                SETTINGS.download(root.map(type), modelUrlInput.value)
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
                width: 140
                height: 30
                label: root.tr("Type")
                entries: ["Checkpoint", "LoRA", "Embedding", "Upscaler"]
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
                placeholder: root.tr("File")
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
                tooltip: root.tr("Select file")
                icon: "qrc:/icons/folder.svg"
                border.color: COMMON.bg4

                onPressed: {
                    uploadFileDialog.open()
                }
                disabled: !root.show
            }

            FileDialog {
                id: uploadFileDialog
                nameFilters: [root.tr("Model files") + " (*.ckpt *.safetensors *.pt *.pth)"]

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
            label: root.tr("Upload")
            onPressed: {
                var file = uploadFileInput.value
                var idx = uploadTypeInput.currentIndex
                var type = uploadTypeInput.model[idx]
                SETTINGS.setUpload(file, idx)
                SETTINGS.upload(root.map(type), file)
            }
            disabled: !root.show
        }

        Item {
            width: parent.width
            height: 30
        }

        Item {
            width: parent.width
            height: 100
            clip: true

            Rectangle {
                width: parent.width / 3
                height: parent.height
                color: COMMON.bg0
                border.color: COMMON.bg4
            }

            ListView {
                id: progressList
                anchors.fill: parent
                anchors.margins: 1
                boundsBehavior: Flickable.StopAtBounds
                model: GUI.network.allDownloads

                delegate: Item {
                    width: parent.width
                    height: 22

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: COMMON.bg4
                    }

                    Item {
                        id: label
                        width: parent.width / 3
                        height: parent.height

                        SToolTip {
                            visible: labelMouseArea.containsMouse
                            delay: 100
                            text: modelData.label
                        }

                        SText {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignLeft
                            leftPadding: 5
                            rightPadding: 5
                            bottomPadding: 2
                            pointSize: 9.5
                            color: COMMON.fg1_5
                            text: modelData.label
                            elide: Text.ElideRight
                        }

                        MouseArea {
                            id: labelMouseArea
                            hoverEnabled: true
                            anchors.fill: parent
                        }
                    }

                    Item {
                        id: bar
                        anchors.left: label.right
                        anchors.right: parent.right
                        height: parent.height

                        property var accent: modelData.error != "" ? 0.0 : (modelData.progress == 1.0 ? 0.6 : 0.2)

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 1
                            anchors.bottomMargin: 2

                            color: "transparent"
                            border.width: 2
                            border.color: COMMON.accent(bar.accent)

                            Rectangle {
                                color: COMMON.accent(bar.accent)
                                opacity: modelData.progress == 0.0 ? 0.2 : 0.1
                                y: 2
                                height: parent.height - 4
                                width: parent.width
                            }

                            SProgress {
                                y: 2
                                height: parent.height - 4
                                width: parent.width
                                working: visible
                                progress: modelData.progress == 0.0 ? -1 : modelData.progress
                                color: COMMON.accent(bar.accent)
                                count: Math.ceil(width/75)
                                duration: width * 10
                                clip: true
                                barWidth: 40
                                opacity: modelData.progress == 0.0 ? 0.5 : 0.7
                            }

                            SText {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                pointSize: 8.85
                                font.bold: true
                                color: COMMON.fg1_5
                                text: {
                                    if(modelData.error != "") {
                                        return root.tr("Failed")
                                    }
                                    if(modelData.progress == 0) {
                                        return root.tr(modelData.type + "ing...")
                                    }
                                    if(modelData.progress == 1.0) {
                                        return root.tr("Done")
                                    }
                                    return (modelData.progress * 100).toFixed(0) + "%"
                                }
                            }

                            SText {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignRight
                                rightPadding: 5
                                pointSize: 8.85
                                font.bold: true
                                color: COMMON.fg1_5
                                text: modelData.eta
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: COMMON.bg4
            }

            Rectangle {
                anchors.fill: parent
                visible: !root.show && progressList.model.length == 0
                color: "#80101010"
            }
        }
    }
}