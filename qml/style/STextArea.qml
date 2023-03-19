import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Rectangle {
    id: root

    property alias text: textArea.text
    property alias font: textArea.font

    color: "transparent"

    Flickable {
        id: control
        anchors.fill: parent
        contentHeight: textArea.height
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        ScrollBar.vertical: SScrollBarV {
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
            wrapMode: TextArea.Wrap
            selectByMouse: true
    
            FontLoader {
                source: "qrc:/fonts/Cantarell-Regular.ttf"
            }
    
            font.pointSize: 10.8
            color: COMMON.fg0

            onCursorRectangleChanged: {
                var y = cursorRectangle.y
                if(y < control.contentY + 5) {
                    control.contentY = y - 5
                }
                if(y >= control.contentY + control.height - 5) {
                    control.contentY = y - control.height + cursorRectangle.height + 5
                }
            }
        }
    }
}