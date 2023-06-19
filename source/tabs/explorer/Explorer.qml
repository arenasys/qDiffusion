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

    function tr(str, file = "Explorer.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    function releaseFocus() {
        parent.releaseFocus()
    }

    Rectangle {
        anchors.fill: column
        color: COMMON.bg0
    }
    
    Flickable {
        id: column
        width: 150
        height: parent.height
        contentHeight: columnContent.height
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        interactive: false

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
        }

        Column {
            id: columnContent
            width: 150

            CategoryButton {
                mode: "favourite"
            }

            Repeater {
                model: ["checkpoint", "component", "lora", "hypernet", "embedding", "upscaler", "wildcard"]

                Column {
                    width: 150
                    CategoryButton {
                        mode: modelData
                        onMove: {
                            moveDialog.show(model, folder, subfolder)
                        }
                    }
                    SubfolderList {
                        mode: modelData
                        onMove: {
                            moveDialog.show(model, folder, subfolder)
                        }
                    }
                }
            }
        }
    }

    MouseArea {
        anchors.fill: column
        acceptedButtons: Qt.NoButton
        onWheel: {
            if(wheel.angleDelta.y < 0) {
                scrollBar.increase()
            } else {
                scrollBar.decrease()
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
                    text: root.tr("Search...")
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
                mode: EXPLORER.currentTab
                label: root.tr(EXPLORER.getLabel(mode), "Category")
                folder: EXPLORER.currentFolder
                search: search.text
                showInfo: EXPLORER.showInfo 
                query: EXPLORER.currentQuery

                onDeleteModel: {
                    deleteDialog.show(model)
                }
            }
        }
    }

    SDialog {
        id: deleteDialog
        title: root.tr("Confirmation")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        property var file: ""

        function show(file) {
            deleteDialog.file = file
            deleteDialog.open()
        }

        height: Math.max(120, deleteMessage.height + 60)
        width: 300

        SText {
            id: deleteMessage
            anchors.centerIn: parent
            padding: 5
            text: root.tr("Delete %1?").arg(deleteDialog.file)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: parent.width
            wrapMode: Text.Wrap
        }       

        onAccepted: {
            EXPLORER.doDelete(deleteDialog.file)
        }

        onClosed: {
            root.forceActiveFocus()
        }
    }

    SDialog {
        id: moveDialog
        title: root.tr("Confirmation")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        property var model: ""
        property var folder: ""
        property var subfolder: ""

        function show(model, folder, subfolder) {
            moveDialog.model = model
            moveDialog.folder = folder
            moveDialog.subfolder = subfolder
            moveDialog.open()
        }

        height: Math.max(120, moveMessage.height + 60)
        width: 300

        SText {
            id: moveMessage
            anchors.centerIn: parent
            padding: 5
            text: root.tr("Move %1?").arg(moveDialog.model)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: parent.width
            wrapMode: Text.Wrap
        }       

        onAccepted: {
            EXPLORER.doMove(moveDialog.model, moveDialog.folder, moveDialog.subfolder)
        }

        onClosed: {
            root.forceActiveFocus()
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_Minus:
                EXPLORER.adjustCellSize(-100)
                break;
            case Qt.Key_Equal:
                EXPLORER.adjustCellSize(100)
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            case Qt.Key_Shift: 
                if(!searchInput.activeFocus) {
                    EXPLORER.showInfo = !EXPLORER.showInfo
                }
                break
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