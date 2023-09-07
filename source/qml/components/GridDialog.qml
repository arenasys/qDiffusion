import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

Dialog {
    id: dialog
    anchors.centerIn: parent
    width: 400
    dim: true
    height: 222
    padding: 5
    closePolicy: Popup.NoAutoClose

    property var source
    
    property alias x_type: x_row.type
    property alias x_value: x_row.value
    property alias x_match: x_row.match

    property alias y_type: y_row.type
    property alias y_value: y_row.value
    property alias y_match: y_row.match

    function tr(str, file = "GridDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    onOpened: {
        enterItem.forceActiveFocus()
    }

    Item {
        id: enterItem
        Keys.onPressed: {
            event.accepted = true
            switch(event.key) {
            case Qt.Key_Enter:
            case Qt.Key_Return:
                dialog.accept()
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }

    background: Item {
        RectangularGlow {
            anchors.fill: bg
            glowRadius: 5
            opacity: 0.75
            spread: 0.2
            color: "black"
            cornerRadius: 10
        }

        Rectangle {
            id: bg
            anchors.fill: parent
            anchors.margins: -1
            color: COMMON.bg1
            border.width: 1
            border.color: COMMON.bg4
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg0
        }
    }

    header: Item {
        implicitHeight: 20
        SText {
            color: COMMON.fg2
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: dialog.title
            font.pointSize: 9
            font.bold: true
        }
        SIconButton {
            color: "transparent"
            icon: "qrc:/icons/eye.svg"
            tooltip: dialog.tr("HMMMM")
            anchors.top: parent.top
            anchors.right: parent.right
            height: 20
            width: 20

            onPressed: {
                //dialog.raw = !dialog.raw
            }
        }
    }

    spacing: 0
    verticalPadding: 0

    footer: Rectangle {
        implicitWidth: parent.width
        implicitHeight: 35
        color: COMMON.bg1
        DialogButtonBox {
            anchors.centerIn: parent
            standardButtons: dialog.standardButtons
            alignment: Qt.AlignHCenter
            spacing: 5

            background: Item {
                implicitHeight: 25
            }

            delegate: Button {
                id: control
                implicitHeight: 25

                contentItem: SText {
                    id: contentText
                    color: COMMON.fg1
                    text: control.text
                    font.pointSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 0
                    color: control.down ? COMMON.bg5 : COMMON.bg4
                    border.color: COMMON.bg6
                }
            }

            onAccepted: dialog.accept()
            onRejected: dialog.reject()
        }
    }

    contentItem: Rectangle {
        id: content
        color: COMMON.bg00
        border.width: 1
        border.color: COMMON.bg5

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
                menuActive: x_suggestions.active
            }

            GridRow {
                id: y_row
                height: 64
                width: parent.width
                label: "Y"
                source: dialog.source
                menuActive: y_suggestions.active
            }
        }

        Suggestions {
            id: x_suggestions
            target: x_row.target
            suggestions: BASIC.gridXSuggestions
            x: x_row.target.mapToItem(content, 0, 0).x + area.cursorRectangle.x;
            y: x_row.target.mapToItem(content, 0, 0).y + area.cursorRectangle.y;
            height: area.cursorRectangle.height
            visible: x_row.type != "None" && area.activeFocus
            property var type: x_row.type
            property alias highlighter: x_row.highlighter
            onTypeChanged: {
                BASIC.gridConfigureRow(type, suggestions, highlighter)
                area.text = area.text + " " //update highlighting
                area.text = area.text.slice(0, -1)
            }
        }

        Suggestions {
            id: y_suggestions
            target: y_row.target
            suggestions: BASIC.gridXSuggestions
            flip: true
            x: y_row.target.mapToItem(content, 0, 0).x + area.cursorRectangle.x;
            y: y_row.target.mapToItem(content, 0, 0).y + area.cursorRectangle.y;
            height: area.cursorRectangle.height
            visible: y_row.type != "None" && area.activeFocus
            property var type: y_row.type
            property alias highlighter: y_row.highlighter
            onTypeChanged: {
                BASIC.gridConfigureRow(type, suggestions, highlighter)
                area.text = area.text + " " //update highlighting
                area.text = area.text.slice(0, -1)
            }
        }
    }
}