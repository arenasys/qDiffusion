import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import gui 1.0
import "../components"

TabButton {
    id: control
    width: implicitWidth
    property var selected: false
    property var working: false

    signal dragEnter()

    contentItem: Item {
        
    }

    background: Item {
        implicitHeight: 40
        implicitWidth: 110
        Rectangle {
            height: 25
            opacity: enabled ? 1 : 0.3
            color: control.down ? COMMON.bg4 : (selected ? COMMON.bg4 : COMMON.bg1_5)
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            clip:true
            Rectangle {
                rotation: 20
                width: parent.height
                height:  2*parent.height
                x: -width
                y: -parent.height
                transformOrigin: Item.BottomRight
                antialiasing: true
                color: COMMON.bg3
            }

            Rectangle {
                rotation: -20
                width: parent.height
                height:  2*parent.height
                x: parent.width+2
                y: -parent.height
                transformOrigin: Item.BottomRight
                antialiasing: true
                color: COMMON.bg3
            }

            SText {
                anchors.fill: parent
                topPadding: 1
                text: control.text
                font.pointSize: 10.9
                opacity: selected ? 1.0 : 0.7
                color: COMMON.fg0
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment:  Text.AlignVCenter
                elide: Text.ElideRight
            }

            LoadingSpinner {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.margins: -10
                anchors.topMargin: -9
                anchors.rightMargin: -4
                source: "qrc:/icons/loading_big.svg"
                width: height
                running: control.working
                duration: 300
                opacity: 0.65
            }
        }

        DropArea {
            anchors.fill: parent
            Timer {
                id: dragTimer
                interval: 200
                onTriggered: {
                    control.dragEnter()
                }
            }
            onEntered: {
                dragTimer.start()
            }
            onExited: {
                dragTimer.stop()
            }
        }
    }
}