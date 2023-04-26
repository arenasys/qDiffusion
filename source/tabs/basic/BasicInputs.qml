import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import Qt.labs.platform 1.1

import gui 1.0
import "../../style"
import "../../components"

Item {
    id: inputArea

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

        Connections {
            target: BASIC
            function onOpenedUpdated() {
                if(BASIC.openedArea == "input") {
                    inputListView.currentIndex = BASIC.openedIndex
                    inputListView.positionViewAtIndex(inputListView.currentIndex, ListView.Center)
                }
            }
        }

        delegate: Item {
            id: item
            height: Math.floor(inputListView.height)
            width: height-9

            onActiveFocusChanged: {
                if(activeFocus) {
                    itemFrame.forceActiveFocus()
                }
            }

            Rectangle {
                id: itemFrame
                anchors.fill: parent
                anchors.margins: 9
                anchors.leftMargin: 0
                color: COMMON.bg00

                property var highlight: activeFocus || inputContextMenu.opened || inputFileDialog.visible || centerDrop.containsDrag
                
                Item {
                    anchors.fill: parent

                    Rectangle {
                        visible: modelData.linked
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: -4
                        anchors.right: trueFrame.left
                        height: parent.height/4
                        color: COMMON.fg2

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            height: 1
                            color: COMMON.fg3
                        }
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: COMMON.fg3
                        }
                    }

                    Rectangle {
                        visible: modelData.linkedTo
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.rightMargin: -5
                        anchors.left: trueFrame.right
                        height: parent.height/4
                        color: COMMON.fg2
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            height: 1
                            color: COMMON.fg3
                        }
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: COMMON.fg3
                        }
                    }


                    RectangularGlow {
                        visible: trueFrame.valid
                        anchors.fill: trueFrame
                        glowRadius: 5
                        opacity: 0.4
                        spread: 0.2
                        color: "black"
                        cornerRadius: 10
                    }

                    TransparencyShader {
                        visible: trueFrame.valid
                        anchors.fill: trueFrame
                    }

                    Item {
                        anchors.fill: parent
                        anchors.margins: 1
                        ImageDisplay {
                            id: itemImage
                            visible: !modelData.empty
                            anchors.fill: parent
                            image: modelData.image
                            centered: true
                        }
                    }

                    Item {
                        id: trueFrame
                        property var valid: itemImage.trueWidth != 0
                        x: valid ? itemImage.trueX + 1: 0
                        y: valid ? itemImage.trueY + 1: 0
                        width: valid ? itemImage.trueWidth : parent.width
                        height: valid ? itemImage.trueHeight : parent.height

                        Rectangle {
                            visible: itemImage.sourceWidth > 0
                            property var factor: parent.width/itemImage.sourceWidth
                            border.color: modelData.extentWarning ? "red" : "#00ff00"
                            border.width: 1
                            color: "transparent"

                            x: modelData.extent.x*factor
                            y: modelData.extent.y*factor
                            width: modelData.extent.width*factor
                            height: modelData.extent.height*factor
                        }
                    }

                    Item {
                        id: borderFrame
                        property var valid: itemImage.trueWidth != 0
                        x: valid ? itemImage.trueX: 0
                        y: valid ? itemImage.trueY: 0
                        width: valid ? itemImage.trueWidth+2 : parent.width
                        height: valid ? itemImage.trueHeight+2 : parent.height

                        Rectangle {
                            anchors.fill: roleLabel
                            color: "#e0101010"
                            border.width: 1
                            border.color: COMMON.bg3
                        }

                        SText {
                            id: roleLabel
                            text: ["", "Image", "Mask", "Subprompts", "Control"][modelData.role]
                            anchors.top: parent.top
                            anchors.left: parent.left
                            leftPadding: 3
                            topPadding: 3
                            rightPadding: 3
                            bottomPadding: 3
                            color: COMMON.fg1_5
                            font.pointSize: 9.8
                        }

                        Rectangle {
                            visible: sizeLabel.text != ""
                            anchors.fill: sizeLabel
                            color: "#e0101010"
                            border.width: 1
                            border.color: COMMON.bg3
                        }

                        SText {
                            id: sizeLabel
                            text: modelData.size
                            anchors.top: parent.top
                            anchors.right: parent.right
                            height: roleLabel.height
                            leftPadding: 3
                            topPadding: 3
                            rightPadding: 3
                            bottomPadding: 3
                            color: COMMON.fg1_5
                            font.pointSize: 9.2
                        }
                    }

                    Rectangle {
                        anchors.fill: borderFrame
                        border.color: itemFrame.highlight ? COMMON.fg2 : COMMON.bg4
                        border.width: 1
                        color: "transparent"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    property var startPosition: Qt.point(0,0)
                    property bool ready: false
                    property var image
                    onPressed: {
                        if (mouse.button == Qt.LeftButton) {
                            inputListView.currentIndex = index
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
                        if(!modelData.empty) {
                            BASIC.open(index, "input")
                        }
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
                            SContextMenuItem {
                                text: "Control"
                                onPressed: {
                                    modelData.role = 4
                                }
                            }
                            /*SContextMenuItem {
                                text: "Subprompt"
                                onPressed: {
                                    modelData.role = 3
                                }
                            }*/
                        }
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 5

                    SIconButton {
                        visible: modelData.empty
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
                        visible: modelData.empty && modelData.role != 1
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
                    width: 10 + 5
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
                    width: parent.width - 20

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
                    width: 10 + 5

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

                Keys.onPressed: {
                    event.accepted = true
                    if(event.modifiers & Qt.ControlModifier) {
                        switch(event.key) {
                        case Qt.Key_C:
                            BASIC.copyItem(index, "input")
                            break;
                        case Qt.Key_V:
                            BASIC.pasteItem(index, "input")
                            break;
                        default:
                            event.accepted = false
                            break;
                        }
                    } else {
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
        }

        header: Item {
            height: parent.height
            width: 9
        }

        footer:  Item {
            height: parent.height
            width: height-9
            Rectangle {
                id: itmFooter
                anchors.fill: parent
                anchors.margins: 9
                anchors.leftMargin: 0
                color: "transparent"
                border.width: 1
                border.color: (itmFooter.activeFocus || addDrop.containsDrag) ? COMMON.bg6 : "transparent"

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

                MouseArea {
                    anchors.fill: parent
                    onPressed: {
                        itmFooter.forceActiveFocus()
                    }
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
                        SContextMenuItem {
                            text: "Subprompts"
                            onPressed: {
                                BASIC.addSubprompt()
                                addContextMenu.close()
                            }
                        }
                        SContextMenuItem {
                            text: "Control"
                            onPressed: {
                                BASIC.addControl()
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

                Keys.onPressed: {
                    event.accepted = true
                    if(event.modifiers & Qt.ControlModifier) {
                        switch(event.key) {
                        case Qt.Key_V:
                            BASIC.pasteItem(-1, "input")
                            break;
                        default:
                            event.accepted = false
                            break;
                        }
                    }
                }
            }
        }
    }
}