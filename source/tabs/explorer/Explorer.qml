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

        SColumnButton {
            label: "Checkpoints"
            property var index: 0
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
            }
        }
        SColumnButton {
            label: "Components"
            property var index: 1
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
            }
        }
        SColumnButton {
            label: "LoRAs"
            property var index: 2
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
            }
        }
        SColumnButton {
            label: "Hypernets"
            property var index: 3
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
            }
        }
        SColumnButton {
            label: "Embeddings"
            property var index: 4
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
            }
        }
        SColumnButton {
            label: "Wildcards"
            property var index: 5
            active: modelsStack.currentIndex == index
            onPressed: {
                modelsStack.currentIndex = index
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
            id: modelsStack
            anchors.fill: parent
            
        }
    }
}