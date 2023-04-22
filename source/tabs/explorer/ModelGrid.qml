import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property var mode: ""
    property var folder: ""
    property var cellSize: 150
    property var shift: false
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: {
            root.deselect(-1)
        }
        onWheel: {
            if(wheel.angleDelta.y < 0) {
                scrollBar.increase()
            } else {
                scrollBar.decrease()
            }
        }
    }

    signal deselect(int index)

    GridView {
        id: modelsView
        property int padding: 10
        property bool showScroll: modelsView.contentHeight > modelsView.height
        cellWidth: Math.max((modelsView.width - 15)/Math.max(Math.ceil((modelsView.width - 5)/root.cellSize), 1), 50)
        cellHeight: Math.floor(cellWidth*1.33)
        anchors.fill: parent
        model: Sql {
            id: modelsSql
            query: "SELECT name, type, desc, file, width, height FROM models WHERE category = '" + root.mode + "' AND folder = '" + root.folder + "' ORDER BY idx ASC;"
            property bool reset: false
            function refresh() {
                modelsView.positionViewAtBeginning()
            }
            onQueryChanged: {
                modelsSql.refresh()
                reset = true
            }
            onResultsChanged: {
                if(reset) {
                    modelsSql.refresh()
                    reset = false
                }
            }
        }

        interactive: false
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
            stepSize: 0.25/Math.ceil(modelsView.count / Math.round(modelsView.width/modelsView.cellWidth))
            policy: modelsView.showScroll ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }

        delegate: Item {
            width: modelsView.cellWidth
            height: modelsView.cellHeight

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
                property var showing: false
                property var editing: false
                property var active: BASIC.parameters.active.includes(sql_name) 

                Connections {
                    target: root
                    function onDeselect(i) {
                        if(i != index) {
                            modelCard.selected = false
                            modelCard.editing = false
                            modelCard.showing = false
                            descText.text = sql_desc
                            labelTextEdit.text = GUI.modelFileName(sql_name)
                        }
                    }
                }

                function select() {
                    modelCard.selected = true
                    root.deselect(index)
                }

                function show() {
                    modelCard.selected = true
                    modelCard.showing = true
                    root.deselect(index)
                }

                function edit() {
                    modelCard.selected = true
                    modelCard.showing = true
                    modelCard.editing = true
                    labelTextEdit.cursorPosition = 0
                    root.deselect(index)
                }

                function save() {
                    EXPLORER.doEdit(sql_name, labelTextEdit.text, descText.text)
                    modelCard.editing = false
                }

                LoadingSpinner {
                    anchors.fill: parent
                    running: sql_width != 0 && thumbnail.status !== Image.Ready
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
                        visible: sql_width == 0 && descText.text == ""
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
                    visible: sql_width != 0
                    anchors.fill: parent
                    anchors.margins: 1
                    property var trueSource: visible ? ("image://async/" + sql_file) : ""
                    source: trueSource
                    fillMode: Image.PreserveAspectCrop
                    cache: false
                    asynchronous: true
                }

                Image {
                    id: fullThumbnail
                    visible: sql_width != 0 && height >= 256
                    anchors.fill: parent
                    anchors.margins: 1
                    property var trueSource: visible ? ("image://big/" + sql_file) : ""
                    source: trueSource
                    fillMode: Image.PreserveAspectCrop
                    cache: false
                    asynchronous: true
                }

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onPressed: {
                        modelCard.select()
                    }
                    onDoubleClicked: {
                        BASIC.parameters.doToggle(sql_name)
                    }
                }

                Item {
                    id: descItem
                    visible: (sql_desc != "" || modelCard.showing) && (sql_width == 0 || modelCard.showing)
                    anchors.fill: interior
                    anchors.margins: 1
                    property var inset: sql_width == 0 ? 2 : 4

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: parent.inset
                        color: COMMON.bg2
                        opacity: sql_width == 0 ? 0 : 0.75
                        border.color: COMMON.bg6
                    }
                    Glow {
                        visible: sql_width != 0
                        opacity: 0.4
                        anchors.fill: descText
                        radius: 5
                        samples: 8
                        color: "#000000"
                        source: descText
                    }
                    STextArea {
                        id: descText
                        anchors.fill: parent
                        anchors.margins: parent.inset
                        readOnly: !modelCard.editing
                        font.pointSize: 9.8
                        area.color: sql_width == 0 ? COMMON.fg2 : COMMON.fg1
                        text: sql_desc
                        scrollBar.opacity: 0.5
                        scrollBar.color: COMMON.fg3

                        area.onActiveFocusChanged: {
                            if(area.activeFocus) {
                                modelCard.select()
                            }
                        }
                    }
                }

                Rectangle {
                    id: typeBg
                    visible: sql_type != ""
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 20
                    opacity: 0.8
                    color: COMMON.bg2
                    border.color: COMMON.bg4

                    Glow {
                        visible: sql_width != 0
                        opacity: 0.4
                        anchors.fill: typeText
                        radius: 5
                        samples: 8
                        color: "#000000"
                        source: typeText
                    }

                    SText {
                        id: typeText
                        anchors.fill: parent
                        text: sql_type
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        color: sql_width != 0 ? COMMON.fg1 : COMMON.fg2
                        elide: Text.ElideRight
                        leftPadding: 5
                        rightPadding: 5
                        font.pointSize: 9.2
                        opacity: 0.8
                    }
                }

                Rectangle {
                    id: labelBg
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 25
                    color: COMMON.bg2
                    opacity: 0.8
                    border.width: sql_width == 0 ? 2 : 1
                    border.color: sql_width == 0 ? COMMON.bg0 : COMMON.bg4

                    Rectangle {
                        visible: sql_width == 0
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
                        onPressed: {
                            modelCard.show()
                        }
                    }
                }


                Item {
                    clip: true
                    anchors.fill: labelBg

                    Glow {
                        property var target: labelTextEdit.visible ? labelTextEdit : labelText
                        visible: sql_width != 0
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

                    SContextMenuItem {
                        text: modelCard.editing ? "Save" : "Edit"
                        onPressed: {
                            if(modelCard.editing) {
                                modelCard.save()
                            } else {
                                modelCard.edit()
                            }
                        }
                    }

                    SContextMenuSeparator {}

                    SContextMenuItem {
                        text: "Visit"
                        onPressed: {
                            EXPLORER.doVisit(sql_name)
                        }
                    }

                    SContextMenuItem {
                        text: "Clear"
                        onPressed: {
                            EXPLORER.doClear(sql_file)
                        }
                    }

                    SContextMenuSeparator {}

                    SContextMenuItem {
                        text: "Delete"
                        onPressed: {
                            deleteDialog.show(sql_name)
                        }
                    }

                    onClosed: {

                    }
                }

                AdvancedDropArea {
                    id: addDrop
                    anchors.fill: parent

                    onDropped: {
                        EXPLORER.doReplace(mimeData, sql_file)
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
    }

    SDialog {
        id: deleteDialog
        title: "Confirmation"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        property var file: ""

        function show(file) {
            deleteDialog.file = file
            deleteDialog.open()
        }

        height: Math.max(120, message.height + 60)
        width: 300

        SText {
            id: message
            anchors.centerIn: parent
            padding: 5
            text: "Delete " + deleteDialog.file + "?"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: parent.width
            wrapMode: Text.Wrap
        }       

        onAccepted: {
            EXPLORER.doDelete(deleteDialog.file)
        }

        onClosed: {
            root.forceActiveFocus()
        }
    }
}