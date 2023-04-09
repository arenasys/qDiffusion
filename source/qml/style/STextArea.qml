import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Rectangle {
    id: root

    property alias text: textArea.text
    property alias font: textArea.font
    property alias monospace: textArea.monospace
    property alias readOnly: textArea.readOnly
    property alias area: textArea

    onActiveFocusChanged: {
        if(root.activeFocus) {
            textArea.forceActiveFocus()
        }
    }
    
    signal tab()

    color: "transparent"

    SContextMenu {
        id: contextMenu
        SContextMenuItem {
            text: "Cut"
            onPressed: {
                textArea.cut()
            }
        }
        SContextMenuItem {
            text: "Copy"
            onPressed: {
                textArea.copy()
            }
        }
        SContextMenuItem {
            text: "Paste"
            onPressed: {
                textArea.paste()
            }
        }
    }

    Flickable {
        id: control
        anchors.fill: parent
        contentHeight: textArea.height
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
            parent: control
            anchors.top: control.top
            anchors.right: control.right
            anchors.bottom: control.bottom
            policy: control.height >= control.contentHeight ? ScrollBar.AlwaysOff : ScrollBar.AlwaysOn
        }

        TextArea {
            id: textArea
            width: parent.width
            height: Math.max(contentHeight+10, root.height)
            padding: 5
            leftPadding: 5
            rightPadding: 10
            wrapMode: TextArea.Wrap
            selectByMouse: true
            persistentSelection: true
            FontLoader {
                source: "qrc:/fonts/Cantarell-Regular.ttf"
            }
            FontLoader {
                source: "qrc:/fonts/SourceCodePro-Regular.ttf"
            }

            property var monospace: false
            font.family: monospace ? "Source Code Pro" : "Cantarell"
            font.pointSize: 10.8
            color: COMMON.fg1

            onCursorRectangleChanged: {
                var y = cursorRectangle.y
                if(y < control.contentY + 5) {
                    control.contentY = y - 5
                }
                if(y >= control.contentY + control.height - 5) {
                    control.contentY = y - control.height + cursorRectangle.height + 5
                }
            }

            Keys.onPressed: {
                event.accepted = true
                if(event.modifiers == 0) {
                    switch(event.key) {
                    case Qt.Key_Tab:
                        root.tab()
                        break;
                    default:
                        break;
                    }
                } else {
                    event.accepted = false
                }
            }
        }

        MouseArea {
            anchors.fill: textArea
            acceptedButtons: Qt.RightButton
            onPressed: {
                contextMenu.popup()
            }
        }
    }
}