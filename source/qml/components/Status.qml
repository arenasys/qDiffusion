import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Rectangle {
    id: root
    
    color: COMMON.bg0

    clip: true
    property var swap: false
    
    height: 48 + progressList.contentHeight

    function tr(str, file = "Status.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    Rectangle {
        id: divider
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 4
        color: COMMON.bg4
    }

    Item {
        anchors.margins: 2
        anchors.top: divider.bottom
        anchors.bottom: parent.bottom
        anchors.left: root.swap ? undefined : parent.left
        anchors.right: root.swap ? parent.right : undefined
        width: Math.max(100, parent.width-4)

        ListView {
            id: progressList
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: contentHeight
            boundsBehavior: Flickable.StopAtBounds
            model: GUI.network.downloads

            delegate: Item {
                width: parent.width
                height: 11
                Rectangle {
                    width: parent.width
                    height: 9                

                    color: "transparent"
                    border.width: 2
                    border.color: COMMON.accent(0.2)

                    SToolTip {
                        visible: mouseArea.containsMouse
                        delay: 100
                        text: modelData.label
                    }

                    SProgress {
                        y: 2
                        height: parent.height - 4
                        x: 2
                        width: parent.width - 4
                        working: visible
                        progress: modelData.progress == 0.0 ? -1 : modelData.progress
                        color: COMMON.accent(0.2)
                        count: 3
                        duration: 1500
                        clip: true
                        barWidth: (width / 4)
                        opacity: modelData.progress == 0.0 ? 1.0 : 0.7
                    }
                    
                    MouseArea {
                        id: mouseArea
                        hoverEnabled: true
                        anchors.fill: parent
                        onPressed: {
                            GUI.currentTab = "Settings"
                            SETTINGS.currentTab = "Remote"
                        }
                    }

                }
            }
        }

        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 40

            color: "transparent"
            border.width: 2
            border.color: [COMMON.accent(0.2), COMMON.accent(0.4), COMMON.accent(0.6), "#a0000000", "#a0000000", COMMON.accent(0.0)][GUI.statusMode]

            SText {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                text: root.tr(GUI.statusText, "Status")
                font.bold: true
            }
        }
    }
}
