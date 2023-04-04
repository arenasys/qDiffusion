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
    }
}