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

    ImageEditor {
        id: editor
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        anchors.bottom: promptDivider.top

        source: "image.png"
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
            anchors.fill: parent
            binding: EDITOR.parameters
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

        onPositivePromptChanged: {
            BASIC.parameters.values.set("prompt", positivePrompt)
        }
        onNegativePromptChanged: {
            BASIC.parameters.values.set("negative_prompt", negativePrompt)
        }
    }

    Rectangle {
        visible: true
        anchors.fill: parent
        color: "#b0101010"
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

    //Keys.forwardTo: [editor]
}