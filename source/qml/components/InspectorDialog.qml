import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

SMovableDialog {
    id: dialog
    title: dialog.tr("Inspect")

    minWidth: 1000
    minHeight: 460
    standardButtons: dialog.anchored ? Dialog.Ok : 0

    property var source

    function tr(str, file = "InspectorDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    onOpened: {
        dialog.setAnchored(true)
    }

    titleItem: SIconButton {
        color: "transparent"
        icon: "qrc:/icons/copy.svg"
        anchors.top: parent.top
        anchors.right: parent.right
        height: 20
        width: 20
        inset: 7
        tooltip: "Copy"

        onPressed: {
            source.copy()
        }
    }

    contentItem: Rectangle {
        id: content
        color: COMMON.bg00
        anchors.fill: parent

        Rectangle {
            id: header
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 30

            color: COMMON.bg0

            Item {
                anchors.fill: parent

                STextInput {
                    id: searchInput
                    anchors.fill: parent
                    color: COMMON.fg0
                    font.bold: false
                    pointSize: 11
                    selectByMouse: true
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 8
                    topPadding: 1

                    onAccepted: {
                        EXPLORER.inspector.search(searchInput.text)
                    }
                }

                SText {
                    text: root.tr("Search...")
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    font.bold: false
                    pointSize: 11
                    leftPadding: 8
                    topPadding: 1
                    color: COMMON.fg2
                    visible: !searchInput.text && !searchInput.activeFocus
                }

                Keys.onPressed: {
                    switch(event.key) {
                    case Qt.Key_Escape:
                        searchInput.text = ""
                        EXPLORER.inspector.search(searchInput.text)
                        break
                    }
                    event.accepted = true
                }
            }
        }

        Item {
            anchors.top: header.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            clip: true

            LoadingSpinner {
                running: EXPLORER.inspector.isLoading
                anchors.centerIn: parent
                width: 200
                height: 200
            }

            SText {
                visible: EXPLORER.inspector.isEmpty
                text: "No Metadata"
                anchors.centerIn: parent
                color: COMMON.fg2
                pointSize: 9.8
            }

            Flickable {
                id: metadataView
                anchors.fill: parent

                contentHeight: dictView.contentHeight
                contentWidth: parent.width
                boundsBehavior: Flickable.StopAtBounds
                interactive: false

                ScrollBar.vertical: SScrollBarV {
                    id: metadataScrollbar
                    policy: ScrollBar.AlwaysOn
                    totalLength: metadataView.contentHeight
                    incrementLength: 45
                }

                Loader {
                    id: dictView
                    property var contentHeight: item == null ? 0 : item.height
                    source: ""
                    width: metadataView.width - 10
                    onLoaded: {
                        item.model = EXPLORER.inspector.model
                    }

                    Connections {
                        target: EXPLORER.inspector
                        function onUpdated() {
                            dictView.source = ""
                            if(!EXPLORER.inspector.isLoading) {
                                dictView.source = "../style/SDictView.qml"
                            }
                        }

                        function onJumpUpdated() {
                            metadataView.contentY = EXPLORER.inspector.jump * 15
                        }
                    }
                }

                Rectangle {
                    visible: metadataView.contentHeight >= 15
                    anchors.left: dictView.left
                    anchors.right: dictView.right
                    anchors.bottom: dictView.bottom
                    height: 1
                    color: COMMON.bg3
                }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                onWheel: {
                    metadataScrollbar.doIncrement(wheel.angleDelta.y)
                }
            }
            
            Rectangle {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.rightMargin: 9
                color: COMMON.bg5
                width: 1
            } 
            
        }

        Rectangle {
            anchors.top: header.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            color: COMMON.bg5
            height: 1
        } 

        Rectangle {
            color: "transparent"
            anchors.fill: parent
            border.width: 1
            border.color: COMMON.bg5
        }
    }
}