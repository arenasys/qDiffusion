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
        height: 62
        width: 300
        OTextInput {
            id: endpointInput
            width: 300
            height: 30
            label: "Endpoint"
            placeholder: "Local"

            bindMap: GUI.config
            bindKey: "endpoint"
        }
        Item {
            width: 300
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
                    text: endpointInput.value == "" ? "Start" : "Connect"
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.fill: parent
                    font.pointSize: 9.8
                    color: COMMON.fg1
                }
            }
        }

        Item {
            width: 300
            height: 30
            Item {
                anchors.fill: parent
                anchors.margins: 2

                SText {
                    text: GUI.statusText
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.fill: parent
                    font.pointSize: 9.8
                    color: COMMON.fg2
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