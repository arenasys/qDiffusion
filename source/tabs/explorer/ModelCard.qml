import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    width: modelsView.cellWidth
    height: modelsView.cellHeight
    property var grid

    function tr(str, file = "ModelCard.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    signal changed()
    signal deleteModel(string model)

    RectangularGlow {
        anchors.fill: modelCard
        glowRadius: 10
        opacity: 0.2
        spread: 0.2
        color: "black"
        cornerRadius: 10
    }

    Rectangle {
        id: modelCard
        anchors.fill: parent
        anchors.leftMargin: modelsView.padding
        anchors.topMargin: modelsView.padding
        color: COMMON.bg1

        property var selected: false
        property var showing: grid.showInfo
        property var editing: false
        property var active: BASIC.parameters.active.includes(sql_name)

        property var info: modelCard.showing || sql_width == 0 || modelCard.editing
        property var desc: (sql_desc != "" && modelCard.showing) || (sql_desc != "" && sql_width == 0) || modelCard.editing

        property var fav: GUI.favourites.includes(sql_name)

        Connections {
            target: grid
            function onShowInfoChanged() {
                modelCard.showing = grid.showInfo
            }
        }

        function setSelected(s) {
            if(modelCard.selected != s) {
                modelCard.selected = s
            }
        }

        Connections {
            target: grid
            function onDeselect(i) {
                if(i != index) {
                    modelCard.setSelected(false)
                    modelCard.editing = false
                    modelCard.showing = grid.showInfo
                    descText.text = Qt.binding(function() { return descText.processedText; })
                    labelTextEdit.text = GUI.modelFileName(sql_name)
                }
            }
        }

        function select() {
            modelCard.setSelected(true)
            grid.deselect(index)
        }

        function hide() {
            modelCard.showing = false
            grid.deselect(index)
        }

        function show() {
            modelCard.setSelected(true)
            modelCard.showing = true
            grid.deselect(index)
        }

        function edit() {
            modelCard.setSelected(true)
            modelCard.showing = true
            modelCard.editing = true
            labelTextEdit.cursorPosition = 0
            grid.deselect(index)
        }

        function save() {
            EXPLORER.doEdit(sql_name, labelTextEdit.text, descText.text)
            modelCard.editing = false
        }

        LoadingSpinner {
            anchors.fill: parent
            running: thumbnail.visible && thumbnail.status !== Image.Ready
        }

        Item {
            id: interior
            anchors.top: typeBg.visible ? typeBg.bottom : parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: labelBg.top
            clip: true
        }
        
        Item {
            anchors.fill: interior
            anchors.bottomMargin: typeBg.visible ? -5 : -10

            Image {
                id: placeholder
                visible: !modelCard.desc
                source: "qrc:/icons/placeholder_black.svg"
                height: parent.width/4
                width: height
                sourceSize: Qt.size(width*1.25, height*1.25)
                anchors.centerIn: parent
            }

            ColorOverlay {
                visible: placeholder.visible
                anchors.fill: placeholder
                source: placeholder
                color: addDrop.containsDrag ? COMMON.fg2 : COMMON.bg4
            }
        }

        Image {
            id: thumbnail
            visible: sql_width != 0 && !modelCard.info
            anchors.fill: parent
            anchors.margins: 1
            property var trueSource: visible ? ((GUI.isCached(sql_file) ? "image://sync/" : "image://async/") + sql_file) : ""
            source: trueSource
            fillMode: Image.PreserveAspectCrop
            cache: false
        }

        Image {
            id: fullThumbnail
            visible: sql_width != 0 && height >= 256 && !modelCard.info
            anchors.fill: parent
            anchors.margins: 1
            property var trueSource: visible ? ("image://big/" + sql_file) : ""
            source: trueSource
            fillMode: Image.PreserveAspectCrop
            cache: false
        }

        Item {
            id: descItem
            visible: modelCard.desc
            anchors.fill: interior
            anchors.margins: 1

            STextArea {
                id: descText
                anchors.fill: parent
                readOnly: !modelCard.editing
                pointSize: 9.8
                area.color: COMMON.fg2
                area.textFormat: TextEdit.AutoText
                property var shortText: (sql_desc.length > grid.descLength ? sql_desc.substring(0, grid.descLength) + "..." : sql_desc)
                property var longText: (sql_desc.length > 10*grid.descLength ? sql_desc.substring(0, 10*grid.descLength) + "..." : sql_desc)
                property var processedText: modelCard.selected ? longText : shortText
                text: descItem.visible ? processedText : ""
                scrollBar.opacity: 0.5
                scrollBar.color: COMMON.fg3

                area.onActiveFocusChanged: {
                    if(area.activeFocus) {
                        contextMenu.input = descText.area
                        modelCard.select()
                    }
                }
                area.onLinkActivated: {
                    GUI.openLink(link)
                }
            }
        }
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton
            preventStealing: true
            property var last: 0
            property var startPosition: null

            onPressed: {
                var now = Date.now()
                if(descItem.visible) {
                    if(now - last >= 200) {
                        mouse.accepted = false
                    }
                }
                last = now
                modelCard.select()
                startPosition = Qt.point(mouse.x, mouse.y)
            }

            onDoubleClicked: {
                BASIC.parameters.doToggle(sql_name)
            }

            onWheel: {
                if(modelCard.selected) {
                    wheel.accepted = false
                } else {
                    scrollBar.doIncrement(wheel.angleDelta.y)
                }
            }

            onReleased: {
                startPosition = null
            }

            onPositionChanged: {
                if(pressed && startPosition) {
                    var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                    if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5) {
                        EXPLORER.doDrag(sql_name)
                        startPosition = null
                    }
                }
            }
        }

        Rectangle {
            id: typeBg
            visible: modelCard.info
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: visible ? 20 : 0
            opacity: 0.8
            color: COMMON.bg2
            border.color: COMMON.bg4

            SText {
                id: typeText
                anchors.fill: parent
                anchors.leftMargin: 21
                anchors.rightMargin: (sql_desc != "" && sql_width != 0) ? 21 : 6
                text: root.tr(sql_display, "Category")
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                color: !modelCard.info ? COMMON.fg1 : COMMON.fg2
                elide: Text.ElideRight
                leftPadding: 5
                rightPadding: 5
                pointSize: 9.2
                opacity: 0.8
            }

            Rectangle {
                anchors.fill: parent
                anchors.bottomMargin: -1
                color: "transparent"
                border.color: COMMON.bg0
                border.width: 1
            }
        }
        
        Rectangle {
            id: labelBg
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 25
            color: "transparent"

            Rectangle {
                anchors.fill: parent
                color: COMMON.bg2
                opacity: 0.8
                border.width: modelCard.info ? 2 : 1
                border.color: modelCard.info ? COMMON.bg0 : COMMON.bg4
            }

            Rectangle {
                visible: modelCard.info
                anchors.fill: parent
                color: "transparent"
                opacity: 0.8
                border.color: COMMON.bg4
            }

            MouseArea {
                id: labelMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton
                onDoubleClicked: {
                    BASIC.parameters.doToggle(sql_name)
                    modelCard.hide()
                }
            }
            SToolTip {
                id: toolTip
                delay: 200
                visible: labelText.truncated && labelMouseArea.containsMouse
                text: labelText.text
            }
        }

        Item {
            clip: true
            anchors.fill: labelBg

            Glow {
                property var target: labelTextEdit.visible ? labelTextEdit : labelText
                visible: !modelCard.info
                opacity: 0.4
                anchors.fill: target
                radius: 5
                samples: 8
                color: "#000000"
                source: target
            }

            SText {
                id: labelText
                visible: !labelTextEdit.visible
                anchors.fill: parent
                text: GUI.modelName(sql_name)
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                color: COMMON.fg1
                elide: Text.ElideRight
                leftPadding: 5
                rightPadding: 5
            }

            STextInput {
                id: labelTextEdit
                visible: modelCard.editing
                anchors.fill: parent
                text: GUI.modelFileName(sql_name)
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                color: COMMON.fg1
                leftPadding: 5
                rightPadding: 5

                onActiveFocusChanged: {
                    if(activeFocus) {
                        contextMenu.input = labelTextEdit
                    }
                }
            }
        }

        MouseArea {
            id: cardMouseArea
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            onPressed: {
                modelCard.select()
                contextMenu.popup()
            }
        }

        SContextMenu {
            id: contextMenu
            width: 80

            property var input: null


            SContextMenuItem {
                text: "Cut"
                visible: modelCard.editing
                height: visible ? 20 : 0
                onPressed: {
                    if(contextMenu.input) {
                        contextMenu.input.cut()
                    }
                }
            }

            SContextMenuItem {
                text: "Copy"
                visible: modelCard.editing
                height: visible ? 20 : 0
                onPressed: {
                    if(contextMenu.input) {
                        contextMenu.input.copy()
                    }
                }
            }

            SContextMenuItem {
                text: "Paste"
                visible: modelCard.editing
                height: visible ? 20 : 0
                onPressed: {
                    if(contextMenu.input) {
                        contextMenu.input.paste()
                    }
                }
            }

            SContextMenuSeparator {
                visible: modelCard.editing
                height: visible ? 11 : 0
            }

            SContextMenuItem {
                text: modelCard.editing ? root.tr("Save", "General") : root.tr("Edit", "General")
                onPressed: {
                    if(modelCard.editing) {
                        modelCard.save()
                    } else {
                        modelCard.edit()
                    }
                }
            }

            SContextMenuItem {
                visible: sql_type != "wildcard"
                text: root.tr("Inspect", "General")
                onPressed: {
                    EXPLORER.inspector.openInspector(sql_name)
                }
            }

            SContextMenuSeparator {}

            SContextMenuItem {
                text: root.tr("Visit", "General")
                onPressed: {
                    EXPLORER.doVisit(sql_name)
                }
            }

            SContextMenuItem {
                text: root.tr("Clear", "General")
                onPressed: {
                    EXPLORER.doClear(sql_file)
                    root.changed()
                }
            }

            SContextMenuSeparator {}

            SContextMenuItem {
                visible: sql_type != "wildcard"
                height: visible ? 20 : 0
                text: root.tr("Prune")
                onPressed: {
                    EXPLORER.doPrune(sql_name)
                }
            }

            SContextMenuItem {
                text: root.tr("Delete", "General")
                onPressed: {
                    root.deleteModel(sql_name)
                }
            }

            SContextMenuSeparator {
                visible: sql_type == "wildcard"
                height: visible ? 13 : 0
            }

            SContextMenuItem {
                visible: sql_type == "wildcard"
                height: visible ? 20 : 0
                text: root.tr("Vocab")
                checkable: true
                checked: GUI.config != null ? GUI.config.get("vocab").includes(sql_name) : false
                onCheckedChanged: {
                    if(checked == GUI.config.get("vocab").includes(sql_name)) {
                        return
                    }
                    if(checked) {
                        BASIC.suggestions.vocabAdd(sql_name)
                    } else {
                        BASIC.suggestions.vocabRemove(sql_name)
                    }
                }
            }
        }

        AdvancedDropArea {
            id: addDrop
            anchors.fill: parent

            onDropped: {
                EXPLORER.doReplace(mimeData, sql_file)
                root.changed()
                thumbnail.source = ""
                fullThumbnail.source = ""
                thumbnail.source = Qt.binding(function() { return thumbnail.trueSource })
                fullThumbnail.source = Qt.binding(function() { return fullThumbnail.trueSource })
            }
        }
    }

    Rectangle {
        anchors.fill: modelCard
        color: "transparent"
        border.width: 2
        border.color: COMMON.bg00
    }

    Item {
        property var frameVisible: modelCard.info
        x: modelCard.x
        y: modelCard.y
        height: 21
        width: height

        Rectangle {
            visible: parent.frameVisible
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.bottomMargin: typeBg.height > 0 ? 2 : 0
            color: "transparent"
            border.color: COMMON.bg0
            border.width: 1
        }
        Rectangle {
            visible: parent.frameVisible
            anchors.fill: parent
            anchors.rightMargin: 1
            anchors.bottomMargin: 1
            color: "transparent"
            border.color: COMMON.bg4
            border.width: 1
        }

        Glow {
            visible: !parent.frameVisible
            opacity: 0.3
            anchors.fill: starButton
            radius: 7
            samples: 8
            color: "#000000"
            source: starButton
        }

        Glow {
            visible: !parent.frameVisible
            opacity: 0.4
            anchors.fill: starButton
            radius: 4
            samples: 8
            color: "#000000"
            source: starButton
        }

        SIconButton {
            id: starButton
            color: parent.frameVisible ? COMMON.bg3 : "transparent"
            iconColor: parent.frameVisible ? COMMON.bg6 : COMMON.fg1_5
            anchors.fill: parent
            anchors.margins: 2
            smooth: false
            inset: 0
            icon: modelCard.fav ? "qrc:/icons/star.svg" : "qrc:/icons/star-outline-big.svg"
            onPressed: {
                GUI.toggleFavourite(sql_name)
            }
        }
    }

    Item {
        visible: sql_desc != "" && sql_width != 0
        property var frameVisible: modelCard.info
        x: modelCard.x + modelCard.width - width
        y: modelCard.y
        height: 21
        width: height

        Rectangle {
            visible: parent.frameVisible
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.bottomMargin: typeBg.height > 0 ? 2 : 0
            anchors.rightMargin: 1
            color: "transparent"
            border.color: COMMON.bg0
            border.width: 1
        }
        Rectangle {
            visible: parent.frameVisible
            anchors.fill: parent
            anchors.leftMargin: 1
            anchors.bottomMargin: 1
            color: "transparent"
            border.color: COMMON.bg4
            border.width: 1
        }

        Glow {
            visible: !parent.frameVisible
            opacity: 0.3
            anchors.fill: infoButton
            radius: 7
            samples: 8
            color: "#000000"
            source: infoButton
        }

        Glow {
            visible: !parent.frameVisible
            opacity: 0.4
            anchors.fill: infoButton
            radius: 4
            samples: 8
            color: "#000000"
            source: infoButton
        }

        SIconButton {
            id: infoButton
            color: parent.frameVisible ? COMMON.bg3 : "transparent"
            iconColor: parent.frameVisible ? COMMON.bg6 : COMMON.fg1_5
            anchors.fill: parent
            anchors.margins: 2
            smooth: false
            inset: 0
            icon: modelCard.showing ? "qrc:/icons/info-big.svg" : "qrc:/icons/info-outline-big.svg"

            onPressed: {
                if (modelCard.showing) {
                    modelCard.hide()
                } else {
                    modelCard.show()
                }
            }
        }
    }

    Rectangle {
        visible: modelCard.active || modelCard.editing
        anchors.fill: modelCard
        anchors.margins: -2
        color: "transparent"
        border.width: 2
        border.color: modelCard.editing ? COMMON.accent(0.25) : COMMON.accent(0)
    }

    Rectangle {
        anchors.fill: modelCard
        color: "transparent"
        border.width: 1
        border.color: modelCard.selected ? COMMON.fg2 : COMMON.bg4
    }
}