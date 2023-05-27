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
    
    property var folder: ""

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

            SColumnButton {
                property var mode: "favourite"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }

            SColumnButton {
                property var mode: "checkpoint"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "checkpoint"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "component"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "component"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "lora"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "lora"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "hypernet"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "hypernet"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "embedding"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "embedding"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "upscaler"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "upscaler"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
                }
            }
            SColumnButton {
                property var mode: "wildcard"
                label: EXPLORER.getLabel(mode)
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                }
            }
            SubfolderList {
                mode: "wildcard"
                label: EXPLORER.getLabel(mode)
                folder: grid.folder
                active: EXPLORER.currentTab == mode
                onPressed: {
                    EXPLORER.currentTab = mode
                    grid.folder = folder
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
                mode: EXPLORER.currentTab
                label: EXPLORER.getLabel(mode)
                folder: ""
                search: search.text

                onModeChanged: {
                    folder = ""
                }
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
            case Qt.Key_Shift: 
                if(!searchInput.activeFocus) {
                    grid.showInfo = !grid.showInfo
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