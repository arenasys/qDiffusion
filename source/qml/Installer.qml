import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

FocusReleaser {
    id: root
    property var window
    property var spinner
    anchors.fill: parent
    
    Component.onCompleted: {
        spinner.visible = false
    }

    function tr(str, file = "Installer.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    Connections {
        target: COORDINATOR
        function onProceed() {
            button.disabled = true
            choice.disabled = true
        }
    }

    Rectangle {
        anchors.fill: parent
        color: COMMON.bg00
    
        Column {
            anchors.centerIn: parent
            width: 300
            height: parent.height - 200

            SText {
                text: root.tr("Requirements")
                width: parent.width
                height: 40
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                pointSize: 10.8
                color: COMMON.fg1
            }

            OChoice {
                id: choice
                width: 300
                height: 30
                label: root.tr("Mode")
                disabled: COORDINATOR.disable
                currentIndex: COORDINATOR.mode
                entries: COORDINATOR.modes
                onCurrentIndexChanged: {
                    currentIndex = currentIndex
                    COORDINATOR.mode = currentIndex
                }

                function display(text) {
                    return root.tr(text)
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
                            totalLength: packageList.contentHeight
                            showLength: packageList.height
                        }

                        delegate: Rectangle {

                            color: (index % 2 == 0 ? COMMON.bg0 : COMMON.bg00)
                            width: packageList.width
                            visible: !(modelData == "pip" || modelData == "wheel")
                            height: visible ? 20 : 0

                            Rectangle {
                                color: "green"
                                anchors.fill: parent
                                opacity: 0.1
                                visible: COORDINATOR.installed.includes(modelData)
                            }


                            SProgress {
                                anchors.fill: parent
                                working: COORDINATOR.progress == -1
                                progress: COORDINATOR.progress
                                color: "yellow"
                                count: Math.ceil(width/60)
                                duration: width * 8
                                clip: true
                                barWidth: 30
                                opacity: 0.1
                                visible: COORDINATOR.installing == modelData
                            }

                            Rectangle {
                                color: "yellow"
                                anchors.fill: parent
                                opacity: 0.05
                                visible: COORDINATOR.installing == modelData
                                onVisibleChanged: {
                                    if(visible) {
                                        packageList.positionViewAtIndex(index, ListView.Contain)
                                    }
                                }
                            }

                            SText {
                                text: modelData.split(" @ ")[0]
                                width: parent.width
                                height: 20
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                pointSize: 9.8
                                color: COMMON.fg1
                            }
                        }
                    }
                }
            }

            SButton {
                id: button
                width: 300
                height: 30
                label: COORDINATOR.disable ? root.tr("Cancel") : (COORDINATOR.packages.length == 0 ? root.tr("Proceed") : root.tr("Install"))
                
                onPressed: {
                    if(!COORDINATOR.disable) {
                        outputArea.text = ""
                    }
                    COORDINATOR.install()
                }   
            }

            SText {
                visible: COORDINATOR.needRestart
                text: root.tr("Restart required")
                width: parent.width
                height: 30
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                pointSize: 9.8
                color: COMMON.fg2
            }

            Item {
                width: parent.width
                height: 30
            }

            Rectangle {
                x: -parent.width
                width: parent.width*3
                height: 120
                border.width: 1
                border.color: COMMON.bg4
                color: "transparent"

                SText {
                    id: versionLabel
                    text: root.tr("Enforce versions?")
                    anchors.bottom: versionCheck.bottom
                    anchors.right: versionCheck.left
                    rightPadding: 7
                    pointSize: 9.8
                    color: COMMON.fg2
                    opacity: 0.9
                }

                Rectangle {
                    id: versionCheck
                    anchors.bottom: parent.top
                    anchors.bottomMargin: 5
                    anchors.right: parent.right
                    height: versionLabel.height
                    width: height
                    border.width: 1
                    border.color: COMMON.bg4
                    color: "transparent"

                    Image {
                        id: versionCheckTick
                        width: 16
                        height: 16
                        visible: COORDINATOR.enforceVersions
                        anchors.centerIn: parent
                        source: "qrc:/icons/tick.svg"
                        sourceSize: Qt.size(parent.width, parent.height)
                    }

                    ColorOverlay {
                        id: color
                        visible: versionCheckTick.visible
                        anchors.fill: versionCheckTick
                        source: versionCheckTick
                        color: COMMON.bg7
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            COORDINATOR.enforceVersions = !COORDINATOR.enforceVersions
                        }
                    }
                }

                STextArea {
                    id: outputArea
                    anchors.fill: parent

                    area.color: COMMON.fg2
                    pointSize: 9.8
                    monospace: true

                    Connections {
                        target: COORDINATOR
                        function onOutput(output) {
                            outputArea.text += output + "\n"
                            outputArea.area.cursorPosition = outputArea.text.length-1
                        }
                    }
                }
            }

        }
    }
}