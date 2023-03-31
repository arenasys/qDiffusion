import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

Item {
    Rectangle {
        anchors.fill: column
        color: COMMON.bg0
    }
    Column {
        id: column
        width: 150
        height: parent.height

        SettingsButton {
            label: "Remote"
            active: settingsStack.currentIndex == 0
            onPressed: {
                settingsStack.currentIndex = 0
            }
        }
    }
    Rectangle {
        id: divider
        anchors.top: column.top
        anchors.bottom: column.bottom
        anchors.left: column.right
        width: 3
        color: COMMON.bg4
    }

    Rectangle {
        anchors.top: column.top
        anchors.bottom: column.bottom
        anchors.left: divider.right
        anchors.right: parent.right
        color: COMMON.bg00

        StackLayout {
            id: settingsStack
            anchors.fill: parent
            RemoteSettings { }
        }
    }
}