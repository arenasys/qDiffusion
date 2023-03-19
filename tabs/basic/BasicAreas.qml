import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import Qt.labs.platform 1.1

import gui 1.0
import "../../style"
import "../../components"

Item {
    id: root
    Flickable {
        anchors.fill: parent
        contentHeight: col.height
        contentWidth: parent.width
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: col
            width: parent.width
            Item {
                id: inputArea
                width: parent.width
                height: Math.max(root.height/2 - 1, 180)

                ListView {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    id: inputListView
                    interactive: false
                    boundsBehavior: Flickable.StopAtBounds
                    clip:true
                    orientation: Qt.Horizontal
                    width: Math.min(contentWidth, parent.width)
                    model: BASIC.inputs
                    ScrollBar.horizontal: SScrollBarH {
                        id: scrollBar
                    }

                    delegate: Item {
                        id: item
                        height: parent.height
                        width: height-9

                        property var image: modelData.image
                        property var role: modelData.role
                        property var empty: modelData.empty
                        property var size: modelData.size

                        RectangularGlow {
                            anchors.fill: itemFrame
                            glowRadius: 5
                            opacity: 0.4
                            spread: 0.2
                            color: "black"
                            cornerRadius: 10
                        }

                        Rectangle {
                            id: itemFrame
                            anchors.fill: parent
                            anchors.margins: 9
                            anchors.leftMargin: 0
                            color: COMMON.bg00

                            property var highlight: activeFocus || inputContextMenu.opened || inputFileDialog.visible || centerDrop.containsDrag
                            
                            TransparencyShader {
                                anchors.centerIn: itemImage
                                width: itemImage.trueWidth
                                height: itemImage.trueHeight
                            }

                            ImageDisplay {
                                id: itemImage
                                visible: !item.empty
                                anchors.fill: parent
                                anchors.margins: 1
                                image: item.image
                                centered: true
                            }

                            Rectangle {
                                anchors.fill: roleLabel
                                height: 22
                                color: "#e0101010"
                                border.width: 1
                                border.color: COMMON.bg3
                            }

                            SText {
                                id: roleLabel
                                text: ["", "Image", "Mask"][item.role]
                                anchors.top: parent.top
                                anchors.left: parent.left
                                leftPadding: 3
                                topPadding: 3
                                rightPadding: 3
                                bottomPadding: 3
                            }

                            Rectangle {
                                visible: sizeLabel.text != ""
                                anchors.fill: sizeLabel
                                height: 22
                                color: "#e0101010"
                                border.width: 1
                                border.color: COMMON.bg3
                            }

                            SText {
                                id: sizeLabel
                                text: item.size
                                anchors.top: parent.top
                                anchors.right: parent.right
                                leftPadding: 3
                                topPadding: 3
                                rightPadding: 3
                                bottomPadding: 3
                                font.pointSize: 9.8
                            }

                            Rectangle {
                                anchors.fill: parent
                                border.color: parent.highlight ? COMMON.fg2 : COMMON.bg4
                                border.width: 1
                                color: "transparent"
                            }

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                property var startPosition: Qt.point(0,0)
                                property bool ready: false
                                property var image
                                onPressed: {
                                    if (mouse.button == Qt.LeftButton) {
                                        itemFrame.forceActiveFocus()
                                        startPosition = Qt.point(mouse.x, mouse.y)
                                        ready = false
                                        itemFrame.grabToImage(function(result) {
                                            image = result.image;
                                            ready = true
                                        })
                                    }
                                    if (mouse.button == Qt.RightButton) {
                                        inputContextMenu.popup()
                                    }
                                }

                                onDoubleClicked: {
                                    canvas.open(modelData)
                                }

                                onPositionChanged: {
                                    if(pressed && ready) {
                                        var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                                        if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5) {
                                            modelData.drag(index, image)
                                        }
                                    }
                                }

                                SContextMenu {
                                    y: 35
                                    id: inputContextMenu
                                    width: 100
                                    SContextMenuItem {
                                        text: modelData.empty ? "Delete" : "Clear"
                                        onPressed: {
                                            if(modelData.empty) {
                                                BASIC.deleteInput(index)
                                            } else {
                                                modelData.clearImage()
                                            }
                                        }
                                    }
                                    SContextMenu {
                                        width: 100
                                        title: "Set role"
                                        SContextMenuItem {
                                            text: "Image"
                                            onPressed: {
                                                modelData.role = 1
                                            }
                                        }
                                        SContextMenuItem {
                                            text: "Mask"
                                            onPressed: {
                                                modelData.role = 2
                                            }
                                        }
                                    }
                                }
                            }

                            Column {
                                anchors.centerIn: parent
                                spacing: 5

                                SIconButton {
                                    visible: item.empty
                                    id: uploadButton
                                    icon: "qrc:/icons/folder.svg"
                                    onPressed: {
                                        itemFrame.forceActiveFocus()
                                        inputFileDialog.open()
                                    }
                                    border.color: COMMON.bg4
                                    border.width: 1
                                    color: COMMON.bg1
                                }

                                SIconButton {
                                    visible: item.empty && modelData.role == 2
                                    id: paintButton
                                    icon: "qrc:/icons/paint.svg"
                                    onPressed: {
                                        itemFrame.forceActiveFocus()
                                        modelData.setImageCanvas()
                                    }
                                    border.color: COMMON.bg4
                                    border.width: 1
                                    color: COMMON.bg1
                                }
                            }

                            FileDialog {
                                id: inputFileDialog
                                nameFilters: ["Image files (*.png *.jpg *.jpeg)"]

                                onAccepted: {
                                    modelData.setImageFile(inputFileDialog.file)
                                }
                            }

                            AdvancedDropArea {
                                id: leftDrop
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width/4
                                anchors.leftMargin: -5

                                onDropped: {
                                    BASIC.addDrop(mimeData, index)
                                }

                                Rectangle {
                                    visible: leftDrop.containsDrag
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: 1
                                    color: COMMON.fg2
                                }
                            }

                            AdvancedDropArea {
                                id: centerDrop
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: parent.width/2

                                onDropped: {
                                    modelData.setImageDrop(mimeData, index)
                                }
                            }

                            AdvancedDropArea {
                                id: rightDrop
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.rightMargin: -5
                                width: parent.width/4

                                onDropped: {
                                    BASIC.addDrop(mimeData, index+1)
                                }

                                Rectangle {
                                    visible: rightDrop.containsDrag
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: 1
                                    color: COMMON.fg2
                                }
                            }

                            Rectangle {
                                visible: modelData.linked
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: -9
                                width: 9
                                height: parent.height/4
                                color: COMMON.fg2
                                border.width: 1
                                border.color: COMMON.fg3
                            }

                            Keys.onPressed: {
                                event.accepted = true
                                switch(event.key) {
                                case Qt.Key_Delete:
                                    if(modelData.empty) {
                                        BASIC.deleteInput(index)
                                    } else {
                                        modelData.clearImage()
                                    }
                                    break;
                                default:
                                    event.accepted = false
                                    break;
                                }
                            }
                        }
                    }

                    header: Item {
                        height: parent.height
                        width: 9
                    }

                    footer:  Item {
                        height: parent.height
                        width: height-9
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 9
                            anchors.leftMargin: 0
                            color: "transparent"
                            border.width: 1
                            border.color: addDrop.containsDrag ? COMMON.bg6 : "transparent"

                            RectangularGlow {
                                anchors.fill: addButton
                                glowRadius: 5
                                opacity: 0.3
                                spread: 0.2
                                color: "black"
                                cornerRadius: 10
                            }

                            Rectangle {
                                anchors.fill: addButton
                                border.color: COMMON.bg4
                                border.width: 1
                                color: COMMON.bg1
                            }

                            SIconButton {
                                id: addButton
                                icon: "qrc:/icons/plus.svg"
                                color: "transparent"
                                anchors.centerIn: parent

                                onPressed: {
                                    addContextMenu.open()
                                }

                                SContextMenu {
                                    y: 35
                                    id: addContextMenu
                                    width: 100
                                    SContextMenuItem {
                                        text: "Image"
                                        onPressed: {
                                            BASIC.addImage()
                                            addContextMenu.close()
                                        }
                                    }
                                    SContextMenuItem {
                                        text: "Mask"
                                        onPressed: {
                                            BASIC.addMask()
                                            addContextMenu.close()
                                        }
                                    }
                                }
                            }

                            AdvancedDropArea {
                                id: addDrop
                                anchors.fill: parent

                                onDropped: {
                                    BASIC.addDrop(mimeData, -1)
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                color: COMMON.bg4
                height: 2
            }

            Item {
                id: outputArea
                y: inputArea.height
                width: parent.width
                height: Math.max(root.height-inputArea.height-2, 180)

                ListView {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    id: outputListView
                    interactive: false
                    boundsBehavior: Flickable.StopAtBounds
                    clip:true
                    orientation: Qt.Horizontal
                    width: Math.min(contentWidth, parent.width)
                    model: BASIC.outputs
                    ScrollBar.horizontal: SScrollBarH { }

                    delegate: Item {
                        id: itemOutput
                        height: outputListView.height
                        width: height-9

                        RectangularGlow {
                            anchors.fill: outputItemFrame
                            glowRadius: 5
                            opacity: 0.4
                            spread: 0.2
                            color: "black"
                            cornerRadius: 10
                        }

                        Rectangle {
                            id: outputItemFrame
                            anchors.fill: parent
                            anchors.margins: 9
                            anchors.leftMargin: 0
                            color: COMMON.bg00

                            property var highlight: activeFocus || outputContextMenu.opened
                            
                            TransparencyShader {
                                anchors.centerIn: outputItemImage
                                width: outputItemImage.trueWidth
                                height: outputItemImage.trueHeight
                            }

                            ImageDisplay {
                                id: outputItemImage
                                visible: !modelData.empty
                                anchors.fill: parent
                                anchors.margins: 1
                                image: modelData.image
                                centered: true
                            }

                            Rectangle {
                                visible: outputSizeLabel.text != ""
                                anchors.fill: outputSizeLabel
                                height: 22
                                color: "#e0101010"
                                border.width: 1
                                border.color: COMMON.bg3
                            }

                            SText {
                                id: outputSizeLabel
                                text: modelData.size
                                anchors.top: parent.top
                                anchors.right: parent.right
                                leftPadding: 3
                                topPadding: 3
                                rightPadding: 3
                                bottomPadding: 3
                                font.pointSize: 9.8
                            }

                            Rectangle {
                                anchors.fill: parent
                                border.color: parent.highlight ? COMMON.fg2 : COMMON.bg4
                                border.width: 1
                                color: "transparent"
                            }

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                property var startPosition: Qt.point(0,0)
                                property bool ready: false
                                property var image
                                onPressed: {
                                    if (mouse.button == Qt.LeftButton) {
                                        outputItemFrame.forceActiveFocus()
                                        startPosition = Qt.point(mouse.x, mouse.y)
                                        ready = false
                                        outputItemFrame.grabToImage(function(result) {
                                            image = result.image;
                                            ready = true
                                        })
                                    }
                                    if (mouse.button == Qt.RightButton) {
                                        outputContextMenu.popup()
                                    }
                                }

                                onDoubleClicked: {
                                    canvas.open(modelData)
                                }

                                onPositionChanged: {
                                    if(pressed && ready) {
                                        var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                                        if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5) {
                                            modelData.drag(index, image)
                                        }
                                    }
                                }

                                SContextMenu {
                                    y: 35
                                    id: outputContextMenu
                                    width: 100
                                    SContextMenuItem {
                                        text: "Delete"
                                        onPressed: {
                                            BASIC.deleteOutput(index)
                                        }
                                    }
                                }
                            }

                            Keys.onPressed: {
                                event.accepted = true
                                switch(event.key) {
                                case Qt.Key_Delete:
                                    BASIC.deleteOutput(index)
                                    break;
                                default:
                                    event.accepted = false
                                    break;
                                }
                            }
                        }
                    }

                    header: Item {
                        height: parent.height
                        width: 9
                    }
                }
            }
        }
    }

    BasicCanvas {
        id: canvas
    }

    Keys.forwardTo: [canvas]
}