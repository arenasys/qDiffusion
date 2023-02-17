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

    

    MovableImageEditor {
        id: editor
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        anchors.bottom: promptDivider.top

        source: "image.png"
//        sourceSize: Qt.size(768, 768)
    }

    SDividerVR {
        id: settingsDivider
        minOffset: 5
        maxOffset: 300
        offset: 200
    }

    Rectangle {
        id: settings
        color: COMMON.bg2
        anchors.left: settingsDivider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }

    SDividerHB {
        id: promptDivider
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        minOffset: 5
        maxOffset: 300
        offset: 200
    }

    Rectangle {
        id: prompt
        color: COMMON.bg2
        anchors.left: parent.left
        anchors.right: settingsDivider.left
        anchors.bottom: parent.bottom
        anchors.top: promptDivider.bottom
    }

    Keys.forwardTo: [editor]
}