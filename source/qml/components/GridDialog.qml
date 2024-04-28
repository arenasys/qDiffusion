import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

SMovableDialog {
    id: dialog
    title: dialog.tr("Grid")
    width: 400
    usualHeight: 180
    standardButtons: dialog.anchored ? (Dialog.Ok | Dialog.Cancel) : Dialog.Apply
    
    property var source
    property var options
    
    property alias x_type: x_row.type
    property alias x_value: x_row.value
    property alias x_match: x_row.match

    property alias y_type: y_row.type
    property alias y_value: y_row.value
    property alias y_match: y_row.match

    property var save_all: GUI.config != null ? GUI.config.get("grid_save_all") : false

    function tr(str, file = "GridDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    onOpened: {
        dialog.setAnchored(true)
    }

    titleItem: SIconButton {
        color: "transparent"
        icon: "qrc:/icons/settings.svg"
        anchors.top: parent.top
        anchors.right: parent.right
        height: 20
        width: 20
        inset: 6

        SContextMenu {
            id: contextMenu
            width: 100
            SContextMenuItem {
                text: dialog.tr("Save all")
                checked: dialog.save_all
                checkable: true
                onCheckedChanged: {
                    if(dialog.save_all != checked) {
                        dialog.save_all = checked
                        GUI.config.set("grid_save_all", checked)
                    }
                }
            }
        }

        onPressed: {
            contextMenu.popup(0,height)
        }
    }

    contentItem: Rectangle {
        id: content
        color: COMMON.bg00
        border.width: 1
        border.color: COMMON.bg5
        anchors.fill: parent

        Column {
            anchors.centerIn: parent
            height: parent.height-30
            width: parent.width-30
            
            GridRow {
                id: x_row
                height: 64
                width: parent.width
                label: "X"
                source: dialog.source
                model: dialog.options
                menuActive: x_suggestions.active
            }

            GridRow {
                id: y_row
                height: 64
                width: parent.width
                label: "Y"
                source: dialog.source
                model: dialog.options
                menuActive: y_suggestions.active
            }
        }

        Suggestions {
            id: x_suggestions
            target: x_row.target
            suggestions: source.gridXSuggestions
            x: x_row.target.mapToItem(content, 0, 0).x + area.cursorRectangle.x;
            y: x_row.target.mapToItem(content, 0, 0).y + area.cursorRectangle.y;
            height: area.cursorRectangle.height
            visible: x_row.type != "None" && area.activeFocus
            property var type: x_row.type
            property alias highlighter: x_row.highlighter
            onTypeChanged: {
                source.gridConfigureRow(type, suggestions, highlighter)
                area.text = area.text + " " //update highlighting
                area.text = area.text.slice(0, -1)
            }
        }

        Suggestions {
            id: y_suggestions
            target: y_row.target
            suggestions: source.gridXSuggestions
            flip: true
            x: y_row.target.mapToItem(content, 0, 0).x + area.cursorRectangle.x;
            y: y_row.target.mapToItem(content, 0, 0).y + area.cursorRectangle.y;
            height: area.cursorRectangle.height
            visible: y_row.type != "None" && area.activeFocus
            property var type: y_row.type
            property alias highlighter: y_row.highlighter
            onTypeChanged: {
                source.gridConfigureRow(type, suggestions, highlighter)
                area.text = area.text + " " //update highlighting
                area.text = area.text.slice(0, -1)
            }
        }
    }
}