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

        Item {
            id: item
            x: Math.floor(parent.item.x)
            y: Math.floor(parent.item.y)
            width: Math.ceil(parent.item.width)
            height: Math.ceil(parent.item.height)
        }

        SGlow {
            visible: movable.item.width > 0
            target: movable.item
        }

        TransparencyShader {
            anchors.fill: item
        }

        AdvancedCanvas {
            id: canvas
            anchors.fill: item
            source: root.source || ""
            smooth: sourceSize.width*2 < width && sourceSize.height*2 < height ? false : true
            brush.color: colorPicker.color

            onNeedsUpdateChanged: {
                if(!cooldown.canvasCooldown) {
                    cooldown.canvasCooldown = true
                    canvas.update()
                }
            }
        }

        MarchingAnts {
            id: selection
            anchors.fill: parent
            offset: Qt.point(canvas.x, canvas.y)
            factor: canvas.width/canvas.sourceSize.width
            selection: canvas.selection
            antialiasing: false

            layer.enabled: true
            layer.effect: MarchingAntsShader {
                fDashStroke: selection.shader
                fDashOffset: selection.dash
            }

            Connections {
                target: canvas.selection
                function onUpdated() { selection.requestUpdate() }
            }

            onNeedsUpdateChanged: {
                if(selection.needsUpdate && !cooldown.selectionCooldown) {
                    cooldown.selectionCooldown = true
                    selection.update()
                }
            }
        }

        Timer {
            id: cooldown
            property var canvasCooldown: false
            property var selectionCooldown: false
            interval: 17; running: true; repeat: true
            onTriggered: {
                if(selection.needsUpdate) {
                    selection.update()
                } else {
                    cooldown.selectionCooldown = false
                }
                if(canvas.needsUpdate) {
                    canvas.update()
                } else {
                    cooldown.canvasCooldown = false
                }
            }
        }

        Timer {
            interval: 100; running: true; repeat: true
            onTriggered: {
                canvas.update()
            }
        }

        Timer {
            interval: 100; running: true; repeat: true
            onTriggered: {
                selection.update()
            }
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true

            function getPosition(mouse) {
                return Qt.point(mouse.x, mouse.y)
            }

            onPressed: {
                canvas.mousePressed(getPosition(mouse), mouse.modifiers)
            }

            onReleased: {
                canvas.mouseReleased(getPosition(mouse), mouse.modifiers)
            }

            onPositionChanged: {
                if(mouse.buttons) {
                    canvas.mouseDragged(getPosition(mouse), mouse.modifiers)
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
        height: brushButton.width * 7

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
            id: rectangleSelectButton
            anchors.left: parent.left
            anchors.top: eraserButton.bottom
            iconColor: canvas.tool == 3 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/rectangle_select.svg"
            onPressed: {
                canvas.tool = 3
            }
        }

        SIconButton {
            id: ellipseSelectButton
            anchors.left: parent.left
            anchors.top: rectangleSelectButton.bottom
            iconColor: canvas.tool == 4 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/ellipse_select.svg"
            onPressed: {
                canvas.tool = 4
            }
        }

        SIconButton {
            id: pathSelectButton
            anchors.left: parent.left
            anchors.top: ellipseSelectButton.bottom
            iconColor: canvas.tool == 5 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/path_select.svg"
            onPressed: {
                canvas.tool = 5
            }
        }

        SIconButton {
            id: moveButton
            anchors.left: parent.left
            anchors.top: pathSelectButton.bottom
            iconColor: canvas.tool == 6 ? COMMON.fg2 : COMMON.bg6
            icon: "qrc:/icons/move.svg"
            onPressed: {
                canvas.tool = 6
            }
        }

        SIconButton {
            anchors.left: parent.left
            anchors.top: moveButton.bottom
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
            id: layerHeader
            y: Math.floor(parent.height /2)
            text: "Layers"
        }

        ListView {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: layerHeader.bottom
            interactive: false
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                id: scrollBar
            }

            verticalLayoutDirection: ListView.BottomToTop
            
            id: layersList
            model: canvas.layers
            height: Math.min(200, contentHeight)
            clip: true

            delegate: Item {
                height: 40
                width: parent.width
                Rectangle {
                    height: 40
                    width: Math.max(40 + thumbnail.width + 24, layersList.width)
                    color: index == canvas.activeLayer ? Qt.darker(COMMON.bg2, 1.25) : COMMON.bg2

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            canvas.activeLayer = index
                        }
                    }

                    SIconButton {
                        id: visibleButton
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.topMargin: 7
                        anchors.bottomMargin: 7
                        width: 40
                        color: "transparent"
                        icon: "qrc:/icons/eye.svg"
                        iconColor: modelData.visible ? COMMON.bg6 : COMMON.bg4

                        onPressed: {
                            modelData.visible = !modelData.visible
                        }
                    }

                    TransparencyShader {
                        anchors.fill: thumbnail
                        gridSize: 5.0
                    }

                    ImageDisplay {
                        id: thumbnail
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.left: visibleButton.right
                        width: height
                        image: modelData.thumbnail
                        centered: true
                        visible: modelData.visible
                    }

                    Rectangle {
                        id: overlay
                        anchors.fill: thumbnail
                        color: "#30000000"
                        visible: false
                    }

                    Blend {
                        visible: !modelData.visible
                        anchors.fill: thumbnail
                        source: thumbnail
                        foregroundSource: overlay
                        mode: "multiply"
                    }

                    Rectangle {
                        anchors.fill: thumbnail
                        color: "transparent"
                        border.color: canvas.activeLayer == index ? "white" : COMMON.bg6
                        border.width: 1
                    }

                    Rectangle {
                        id: labelBackground
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.left: thumbnail.right
                        anchors.right: parent.right
                        anchors.margins: 7

                        clip: true

                        color: label.activeFocus ? Qt.darker(parent.color, 1.15) : "transparent"
                        border.color: label.activeFocus ? Qt.lighter(parent.color, 1.15) : "transparent"
                        border.width: 1.5

                        STextInput {
                            id: label
                            color: modelData.visible ? COMMON.fg0 : COMMON.fg2
                            activeFocusOnPress: false
                            anchors.fill: parent
                            leftPadding: 5
                            rightPadding: 5
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.name
                        }

                        MouseArea {
                            anchors.fill: parent
                            visible: !label.activeFocus
                            onDoubleClicked: {
                                label.forceActiveFocus()
                                label.selectAll()
                            }
                            onPressed: {
                                canvas.activeLayer = index
                            }
                        }
                    }
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