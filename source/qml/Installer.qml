import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

FocusReleaser {
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: COMMON.bg00
    
        Column {
            anchors.centerIn: parent
            width: 300
            height: parent.height - 200

            SText {
                text: "Requirements"
                width: parent.width
                height: 40
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 10.8
                color: COMMON.fg1
            }

            OChoice {
                width: 300
                height: 30
                label: "Mode"
                disabled: COORDINATOR.disable
                currentIndex: COORDINATOR.mode
                model: ["Nvidia", "AMD", "Remote"]
                onCurrentIndexChanged: {
                    currentIndex = currentIndex
                    COORDINATOR.mode = currentIndex
                }
            }

            Item {
                width: 300
                height: 200
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    anchors.bottomMargin: 0
                    border.color: COMMON.bg4
                    color: "transparent"
                    ListView {
                        id: packageList
                        anchors.fill: parent
                        anchors.margins: 1
                        clip: true
                        model: COORDINATOR.packages
                        boundsBehavior: Flickable.StopAtBounds

                        ScrollBar.vertical: SScrollBarV {
                            id: scrollBar
                            policy: packageList.contentHeight > packageList.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                        }

                        delegate: Rectangle {

                            color: (index % 2 == 0 ? COMMON.bg0 : COMMON.bg00)
                            width: packageList.width
                            height: 20

                            Rectangle {
                                color: "green"
                                anchors.fill: parent
                                opacity: 0.1
                                visible: COORDINATOR.installed.includes(modelData)
                            }

                            Rectangle {
                                color: "yellow"
                                anchors.fill: parent
                                opacity: 0.1
                                visible: COORDINATOR.installing == modelData
                                onVisibleChanged: {
                                    if(visible) {
                                        packageList.positionViewAtIndex(index, ListView.Contain)
                                    }
                                }
                            }

                            SText {
                                text: modelData
                                width: parent.width
                                height: 20
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pointSize: 9.8
                                color: COMMON.fg1
                            }
                        }
                    }
                }
            }

            SButton {
                width: 300
                height: 30
                label: COORDINATOR.disable ? "Cancel" : (COORDINATOR.packages.length == 0 ? "Proceed" : "Install")
                
                onPressed: {
                    COORDINATOR.install()
                }   
            }

            SText {
                visible: COORDINATOR.needRestart
                text: "Restart required"
                width: parent.width
                height: 30
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9.8
                color: COMMON.fg2
            }

        }
    }
}