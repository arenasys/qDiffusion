import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {

    Column {
        anchors.centerIn: parent
        height: parent.height-100
        width: parent.width/2
        OTextInput {
            id: endpointInput
            width: parent.width
            height: 30
            label: "Endpoint"
            placeholder: "Local"

            bindMap: GUI.config
            bindKey: "endpoint"
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

        Item {
            width: parent.width
            height: 30
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                color: mouseArea.containsPress ? COMMON.bg4 : COMMON.bg3
                border.color: mouseArea.containsMouse ? COMMON.bg5 : COMMON.bg4

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true

                    onPressed: {
                        SETTINGS.restart()
                    }
                }

                SText {
                    text: "Restart"
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.fill: parent
                    font.pointSize: 9.8
                    color: COMMON.fg1
                }
            }
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
                model: ["SD", "LoRA", "HN", "TI", "SR"]
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
            }
        }
        Item {
            width: parent.width
            height: 30
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                color: mouseArea2.containsPress ? COMMON.bg4 : COMMON.bg3
                border.color: mouseArea2.containsMouse ? COMMON.bg5 : COMMON.bg4

                MouseArea {
                    id: mouseArea2
                    anchors.fill: parent
                    hoverEnabled: true

                    onPressed: {
                        SETTINGS.download(modelTypeInput.model[modelTypeInput.currentIndex], modelUrlInput.value)
                    }
                }

                SText {
                    text: "Download"
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.fill: parent
                    font.pointSize: 9.8
                    color: COMMON.fg1
                }
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