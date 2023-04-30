import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import Qt.labs.platform 1.1

import gui 1.0
import "../../style"
import "../../components"

Item {
    id: area

    ListView {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        id: listView
        interactive: false
        boundsBehavior: Flickable.StopAtBounds
        highlightFollowsCurrentItem: BASIC.openedArea == "output"
        clip:true
        orientation: Qt.Horizontal
        width: Math.min(contentWidth, parent.width)
        model: Sql {
            id: outputsSql
            query: "SELECT id FROM outputs ORDER BY id DESC;"
        }
        ScrollBar.horizontal: SScrollBarH { 
            id: scrollBar
            stepSize: 1/(4*Math.ceil(outputsSql.length))
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: {
                if(wheel.angleDelta.y < 0) {
                    scrollBar.increase()
                } else {
                    scrollBar.decrease()
                }
            }
        }


        Connections {
            target: BASIC
            function onOpenedUpdated() {
                if(BASIC.openedArea == "output") {
                    listView.currentIndex = BASIC.outputIDToIndex(BASIC.openedIndex)
                    listView.positionViewAtIndex(listView.currentIndex, ListView.Center)
                }
            }
        }

        delegate: Item {
            id: item
            height: Math.floor(listView.height)
            width: height-9
            property var modelObj: BASIC.outputs(sql_id)
            property var artifacts: modelObj.artifacts
            property var aIndex: -1
            property var aName: aIndex == -1 ? "" : artifacts[aIndex]
            property var img: aIndex == -1 ? modelObj.image : modelObj.artifact(aName)

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
                clip: true

                property var highlight: activeFocus || contextMenu.opened

                RectangularGlow {
                    anchors.fill: trueFrame
                    glowRadius: 5
                    opacity: 0.4
                    spread: 0.2
                    color: "black"
                    cornerRadius: 10
                }

                ImageDisplay {
                    id: itemImage
                    visible: !modelObj.empty
                    anchors.fill: parent
                    image: item.img
                    centered: true
                    smooth: implicitWidth > trueWidth && implicitHeight > trueHeight
                }
                
                Item {
                    id: trueFrame
                    x: itemImage.trueX
                    y: itemImage.trueY
                    width: itemImage.trueWidth
                    height: itemImage.trueHeight

                    Rectangle {
                        anchors.fill: nameLabel
                        visible: nameLabel.text != ""
                        color: "#e0101010"
                        border.width: 1
                        border.color: COMMON.bg3
                    }

                    SText {
                        id: nameLabel
                        text: item.aName
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
                        anchors.fill: indexLabel
                        visible: indexLabel.text != ""
                        color: "#e0101010"
                        border.width: 1
                        border.color: COMMON.bg3
                    }

                    SText {
                        id: indexLabel
                        text: item.artifacts.length != "" ? ((item.aIndex+2) + " of " + (item.artifacts.length + 1)) : ""
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
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
                        text: itemImage.implicitWidth + "x" + itemImage.implicitHeight
                        anchors.top: parent.top
                        anchors.right: parent.right
                        leftPadding: 3
                        topPadding: 3
                        rightPadding: 3
                        bottomPadding: 3
                        color: COMMON.fg1_5
                        font.pointSize: 9.2
                    }

                    Rectangle {
                        anchors.fill: parent
                        border.color: itemFrame.highlight ? COMMON.fg2 : COMMON.bg4
                        border.width: 1
                        color: "transparent"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    property var startPosition: Qt.point(0,0)
                    onPressed: {
                        if (mouse.button == Qt.LeftButton) {
                            listView.currentIndex = index
                            itemFrame.forceActiveFocus()
                            startPosition = Qt.point(mouse.x, mouse.y)
                        }
                        if (mouse.button == Qt.RightButton && modelObj.ready) {
                            contextMenu.popup()
                        }
                    }

                    onDoubleClicked: {
                        BASIC.open(sql_id, "output")
                    }

                    onPositionChanged: {
                        if(pressed) {
                            var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                            if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5 && modelObj.ready) {
                                modelObj.drag()
                            }
                        }
                    }

                    SContextMenu {
                        y: 35
                        id: contextMenu
                        width: 100
                        SContextMenuItem {
                            text: "Clear"
                            onPressed: {
                                BASIC.deleteOutput(sql_id)
                            }
                        }
                        SContextMenuItem {
                            text: "Clear to right"
                            onPressed: {
                                BASIC.deleteOutputAfter(sql_id)
                            }
                        }

                        SContextMenuSeparator { }

                        SContextMenuItem {
                            text: "Open"
                            onTriggered: {
                                GALLERY.doOpenImage([modelObj.file])
                            }
                        }

                        SContextMenuItem {
                            text: "Visit"
                            onTriggered: {
                                GALLERY.doOpenFolder([modelObj.file])
                            }
                        }

                        SContextMenuSeparator { }

                        Sql {
                            id: destinationsSql
                            query: "SELECT name, folder FROM folders WHERE UPPER(name) != UPPER('" + modelObj.mode + "');"
                        }

                        SContextMenu {
                            id: copyToMenu
                            title: "Copy to"
                            Instantiator {
                                model: destinationsSql
                                SContextMenuItem {
                                    text: sql_name
                                    onTriggered: {
                                        GALLERY.doCopy(sql_folder, [modelObj.file])
                                    }
                                }
                                onObjectAdded: copyToMenu.insertItem(index, object)
                                onObjectRemoved: copyToMenu.removeItem(object)
                            }
                        }
                    }
                }

                MouseArea {
                    anchors.right: trueFrame.right
                    anchors.bottom: trueFrame.bottom
                    width: indexLabel.width
                    height: indexLabel.height
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onPressed: {
                        if (mouse.button == Qt.LeftButton) {
                            if(item.aIndex == item.artifacts.length-1) {
                                item.aIndex = -1
                            } else {
                                item.aIndex += 1
                            }
                        } else {
                            if(item.aIndex == -1) {
                                item.aIndex = item.artifacts.length-1
                            } else {
                                item.aIndex -= 1
                            }
                        }
                    }
                }

                AdvancedDropArea {
                    anchors.fill: parent
                }

                Keys.onPressed: {
                    event.accepted = true
                    if(event.modifiers & Qt.ControlModifier) {
                        switch(event.key) {
                        case Qt.Key_C:
                            modelObj.copy()
                            break;
                        default:
                            event.accepted = false
                            break;
                        }
                    } else {
                        switch(event.key) {
                        case Qt.Key_Delete:
                            BASIC.deleteOutput(sql_id)
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
    }
}