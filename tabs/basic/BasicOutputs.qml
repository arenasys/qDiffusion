import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import Qt.labs.platform 1.1

import gui 1.0
import "../../style"
import "../../components"

Item {
    id: outputArea
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
        model: Sql {
            id: foldersSql
            query: "SELECT id FROM outputs ORDER BY id DESC;"
        }
        ScrollBar.horizontal: SScrollBarH { }

        delegate: Item {
            id: itemOutput
            height: outputListView.height
            width: height-9
            property var modelObj: BASIC.outputs(sql_id) 

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
                    visible: !modelObj.empty
                    anchors.fill: parent
                    anchors.margins: 1
                    image: modelObj.image
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
                    text: modelObj.size
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
                        canvas.open(modelObj)
                    }

                    onPositionChanged: {
                        if(pressed && ready) {
                            var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                            if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5) {
                                modelObj.drag(sql_id, image)
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
                                BASIC.deleteOutput(sql_id)
                            }
                        }
                    }
                }

                Keys.onPressed: {
                    event.accepted = true
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

        header: Item {
            height: parent.height
            width: 9
        }
    }
}