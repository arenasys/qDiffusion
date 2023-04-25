import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

ListView {
    id: root
    interactive: false
    width: parent.width
    height: contentHeight
    property var index: 0
    property var mode: ""
    property var stack
    model: Sql {
        query: "SELECT DISTINCT folder FROM models WHERE category = '" + root.mode + "' AND folder != '' ORDER BY folder ASC;"
    }
    delegate: Item {
        x: 10
        width: root.width - 2*x
        height: 25
        SColumnButton {
            id: button
            label: modelData
            height: 25
            width: parent.width
            active: root.stack.currentIndex == root.index && root.stack.currentItem.folder == modelData
            onPressed: {
                root.stack.currentIndex = root.index
                root.stack.currentItem.folder = modelData
            }
        }
    }
}