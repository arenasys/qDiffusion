import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import Qt.labs.platform 1.1

import gui 1.0
import "../../style"
import "../../components"

Item {
    id: root
    Flickable {
        anchors.fill: parent
        contentHeight: col.height
        contentWidth: parent.width
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: col
            width: parent.width

            BasicInputs {
                id: inputArea
                width: parent.width
                height: Math.max(root.height/2 - 1, 180)
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                color: COMMON.bg4
                height: 2
            }

            BasicOutputs {
                id: outputArea
                y: inputArea.height
                width: parent.width
                height: Math.max(root.height-inputArea.height-2, 180)
            }
        }
    }

    BasicFull {
        id: canvas
    }

    Keys.forwardTo: [canvas]
}