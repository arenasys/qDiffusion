import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.0

import gui 1.0

import "../style"

Item {
    id: root
    clip: true

    property var source
    property var sourceSize

    Rectangle {
        anchors.fill: root
        color: COMMON.bg0
    }

    SShadow {
        anchors.fill: movable
    }

    MovableItem {
        id: movable
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: toolSettingsDivider.right
        anchors.right: layersDivider.left
        itemWidth: canvas.sourceSize.width
        itemHeight: canvas.sourceSize.height
        ctrlZoom: true

        SGlow {
            visible: movable.item.width > 0
            target: movable.item
        }

        TransparencyBackground {
            anchors.fill: parent.item
        }

        ImageEditor {
            id: canvas
            anchors.fill: parent.item
            source: root.source || ""
            smooth: sourceSize.width*2 < width && sourceSize.height*2 < height ? false : true
            brush.color: colorPicker.color

            Component.onCompleted: {
                
            }
        }
        
        Timer {
            interval: 17; running: true; repeat: true
            onTriggered: canvas.update()
        }

        MouseArea {
            id: mouseArea
            anchors.fill: canvas
            hoverEnabled: true

            function getPosition(mouse) {
                var wf = canvas.sourceSize.width/width
                var hf = canvas.sourceSize.height/height
                return Qt.point(mouse.x*wf, mouse.y*hf)
            }

            onPressed: {
                canvas.mousePressed(getPosition(mouse))
            }

            onReleased: {
                canvas.mouseReleased(getPosition(mouse))
            }

            onPositionChanged: {
                if(mouse.buttons) {
                    canvas.mouseDragged(getPosition(mouse))
                }
            }
        }
    }

    SGlow {
        target: toolBarHolder
    }

    Rectangle {
        id: toolBarHolder
        anchors.fill: toolBar
        anchors.margins: -3
        color: COMMON.bg4
    }

    Rectangle {
        id: toolBar
        color: COMMON.bg2
        anchors.left: toolSettingsDivider.right
        anchors.verticalCenter: toolSettingsDivider.verticalCenter
        width: brushButton.width
        height: brushButton.width * 3

        SIconButton {
            id: brushButton
            anchors.left: parent.left
            anchors.top: parent.top
            iconColor: canvas.tool == 1 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/brush.svg"
            onPressed: {
                canvas.tool = 1
            }
        }

        SIconButton {
            id: eraserButton
            anchors.left: parent.left
            anchors.top: brushButton.bottom
            iconColor: canvas.tool == 2 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/eraser.svg"
            onPressed: {
                canvas.tool = 2
            }
        }

        SIconButton {
            anchors.left: parent.left
            anchors.top: eraserButton.bottom
            icon: "qrc:/icons/refresh.svg"
            onPressed: {
                canvas.load()
            }
        }
    }

    SDividerVL {
        id: toolSettingsDivider
        offset: 200
        minOffset: 0
        maxOffset: 300
    }

    Rectangle {
        id: toolSettings
        color: COMMON.bg0_5
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: toolSettingsDivider.left

        width: Math.max(150, toolSettingsDivider.x)

        SHeader {
            id: colorPickerHeader
            anchors.top: parent.top
            hasDivider: false
            text: "Color Picker"
        }

        ColorPicker {
            id: colorPicker
            anchors.right: parent.right
            anchors.left: parent.left
            anchors.top: colorPickerHeader.bottom
            height: width
        }

        SHeader {
            id: brushSettingsHeader
            anchors.top: colorPicker.bottom
            text: "Brush Settings"
        }
    }

    SDividerVR {
        id: layersDivider
        offset: 200
        minOffset: 5
        maxOffset: 300
    }
    
    Rectangle {
        id: layers
        color: COMMON.bg2
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: layersDivider.right
        width: layersDivider.offset

        SHeader {
            anchors.top: layers.top
            text: "Current Layer"
            hasDivider: false
        }

        SHeader {
            anchors.bottom: layersList.top
            text: "Layers"
        }

        ListView {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            id: layersList
            model: canvas.layers
            height: Math.max(200, 50*canvas.layers.length)
            clip: true

            delegate: Rectangle {
                height: 50
                width: parent.width
                color: index == canvas.activeLayer ? Qt.darker(COMMON.bg2, 1.25) : COMMON.bg2

                SIconButton {
                    id: visibleButton
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.topMargin: 10
                    anchors.bottomMargin: 10
                    width: 40
                    color: "transparent"
                    icon: "qrc:/icons/eye.svg"
                    iconColor: modelData.visible ? COMMON.bg6 : COMMON.bg4

                    onPressed: {
                        modelData.visible = !modelData.visible
                    }
                }

                ImageDisplay {
                    id: thumbnail
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: visibleButton.right
                    width: height
                    image: modelData.thumbnail
                    centered: true
                }

                MouseArea {
                    anchors.left: visibleButton.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    onPressed: {
                        canvas.activeLayer = index
                    }
                }

                Rectangle {
                    anchors.fill: label
                    color: label.activeFocus ? Qt.darker(parent.color, 1.15) : parent.color
                }


                STextInput {
                    id: label
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: thumbnail.right
                    anchors.right: parent.right
                    anchors.margins: 12
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                    text: modelData.name
                }
            }
        }
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_Z:
                canvas.undo()
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            default:
                event.accepted = false
                break;
            }
        }
    }
}