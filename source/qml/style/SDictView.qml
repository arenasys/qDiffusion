import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Column {
    id: root
    property var model
    property var offset: 0

    onModelChanged: {
        if(model != null) {
            repeater.model = model.keys
        } else {
            repeater.model = []
        }
    }
    
    Repeater {
        id: repeater
        model: []

        delegate: Item {
            width: root.width
            height: (leaf ? 1 : Math.max(root.model.leaves(modelData), 1)) * 15

            property var leaf: root.model.isLeaf(modelData)
            property var mod: (index+offset) % 2
            property var key_width: Math.min(Math.max(40, root.model.width * 8), 300) + 10
            property var marked: root.model.markers.includes(modelData)

            clip: true

            Item {
                height: 15
                width: key_width

                STextSelectable {
                    anchors.fill: parent
                    text: modelData
                    color: COMMON.fg2
                    monospace: true
                    pointSize: 9.5
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.75
                }
            }

            Rectangle {
                visible: parent.leaf
                x: key_width
                height: parent.height
                width: key_width, parent.width - key_width
                color: leaf && mod == 0 ? COMMON.bg1 : COMMON.bg0
                STextSelectable {
                    anchors.fill: parent
                    text: root.model.getLeaf(modelData)
                    color: COMMON.fg2
                    monospace: true
                    leftPadding: 5
                    rightPadding: 5
                    pointSize: 9.5
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                }
            }


            Rectangle {
                anchors.left:parent.left
                anchors.right:parent.right
                anchors.top:parent.top
                color: COMMON.bg3
                height: 1
            }

            Rectangle {
                anchors.top:parent.top
                anchors.bottom:parent.bottom
                anchors.left:parent.left
                color: COMMON.bg3
                width: 1
            }

            Rectangle {
                x: key_width
                height: 15
                width: 1
                color: COMMON.bg3
            }

            Item {
                id: child
                visible: !parent.leaf
                x: key_width
                width: parent.width - key_width
                height: parent.height

                property var model: root.model.getDict(modelData) 
                Loader {
                    source: "SDictView.qml"
                    width: child.width
                    onLoaded: {
                        item.model = child.model
                        item.offset = mod
                    }
                }
            }

            Rectangle {
                color: "transparent"
                anchors.fill: parent
                border.color: COMMON.accent(0)
                border.width: 2
                visible: marked
            }
        }
    }
}