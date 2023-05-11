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

    property var label: "Checkpoints"
    property var mode: "checkpoint"
    property var folder: ""

    function releaseFocus() {
        parent.releaseFocus()
    }

    Rectangle {
        anchors.fill: column
        color: COMMON.bg0
    }
    Column {
        id: column
        width: 150
        height: parent.height

        SColumnButton {
            property var mode: "checkpoint"
            label: "Checkpoints"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "checkpoint"
            label: "Checkpoints"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
            }
        }
        SColumnButton {
            property var mode: "component"
            label: "Components"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "component"
            label: "Components"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
            }
        }
        SColumnButton {
            property var mode: "lora"
            label: "LoRAs"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "lora"
            label: "LoRAs"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
            }
        }
        SColumnButton {
            property var mode: "hypernet"
            label: "Hypernets"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "hypernet"
            label: "Hypernets"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
            }
        }
        SColumnButton {
            property var mode: "embedding"
            label: "Embeddings"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "embedding"
            label: "Embeddings"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
            }
        }
        SColumnButton {
            property var mode: "wildcard"
            label: "Wildcards"
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = ""
            }
        }
        SubfolderList {
            mode: "wildcard"
            label: "Wildcards"
            folder: root.folder
            active: root.mode == mode
            onPressed: {
                root.label = label
                root.mode = mode
                root.folder = folder
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
        clip: true

        Rectangle {
            id: search
            width: parent.width
            height: 30
            color: COMMON.bg1

            property var text: searchInput.text

            Item {
                anchors.fill: parent
                anchors.bottomMargin: 2

                STextInput {
                    id: searchInput
                    anchors.fill: parent
                    color: COMMON.fg0
                    font.bold: false
                    font.pointSize: 11
                    selectByMouse: true
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 8
                    topPadding: 1

                    onAccepted: {
                        root.releaseFocus()
                    }
                }

                SText {
                    text: "Search..."
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    font.bold: false
                    font.pointSize: 11
                    leftPadding: 8
                    topPadding: 1
                    color: COMMON.fg2
                    visible: !searchInput.text && !searchInput.activeFocus
                }
            }
        
            Rectangle {
                width: parent.width
                anchors.bottom: parent.bottom
                height: 2
                color: COMMON.bg4
            }
        }
        Item {
            clip: true
            anchors.fill: parent
            anchors.topMargin: search.height

            ModelGrid {
                id: grid
                anchors.fill: parent
                label: root.label
                mode: root.mode
                folder: root.folder
                search: search.text
            }
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_Minus:
                if(grid.cellSize > 150) {
                    grid.cellSize -= 100
                }
                break;
            case Qt.Key_Equal:
                if(grid.cellSize < 450) {
                    grid.cellSize += 100
                }
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            case Qt.Key_Escape:
                if(searchInput.activeFocus) {
                    search.text = ""
                    searchInput.text = ""
                    root.releaseFocus()
                }
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }
}