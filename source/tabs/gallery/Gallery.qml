import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"

Rectangle {
    id: root
    color: COMMON.bg0
    clip: true
    property var asleep: true

    function tr(str, file = "Gallery.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    Connections {
        target: GUI
        function onCurrentTabChanged() {
            if(GUI.currentTab == "History") {
                root.asleep = false
            }
        }
    }

    function releaseFocus() {
        parent.releaseFocus()
    }

    SDialog {
        id: deleteDialog
        title: root.tr("Confirmation")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        property var files: []

        function show(files) {
            deleteDialog.files = files
            deleteDialog.open()
        }

        height: 120

        SText {
            anchors.fill: parent
            padding: 5
            text: root.tr("Delete %1 images?").arg(deleteDialog.files.length)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }       

        onAccepted: {
            GALLERY.doDelete(deleteDialog.files)
        }

        onClosed: {
            root.forceActiveFocus()
        }

    }

    Item {
        anchors.top: parent.top
        anchors.left: galleryDivider.right
        height: Math.max(200, parent.height)
        width: Math.max(210, parent.width - galleryDivider.x - 5)

        SComboBox {
            id: folder
            width: Math.min(gallery.width, 120)
            anchors.top: parent.top
            anchors.right: parent.right
            clip: true

            textRole: "sql_name"
            valueRole: "sql_folder"

            model: Sql {
                id: foldersSql
                query: "SELECT name, folder FROM folders;"
            }

            onCurrentIndexChanged: {
                root.releaseFocus()
            }
        }

        Rectangle {
            id: folderDivider
            anchors.top: folder.top
            anchors.bottom: folder.bottom
            anchors.right: folder.left
            width: 3
            color: COMMON.bg4
        }

        Rectangle {
            id: search
            anchors.left: parent.left
            anchors.right: folderDivider.left
            height: 30
            color: COMMON.bg1
            clip: true

            property var text: ""
            
            STextInput {
                id: searchInput
                anchors.fill: parent
                color: COMMON.fg0
                font.bold: false
                font.pointSize: 11
                selectByMouse: true
                verticalAlignment: Text.AlignVCenter
                leftPadding: 8
                topPadding: 1

                onAccepted: {
                    search.text = searchInput.text
                    root.releaseFocus()
                }
            }

            SText {
                text: root.tr("Search...")
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                font.bold: false
                font.pointSize: 11
                leftPadding: 8
                topPadding: 1
                color: COMMON.fg2
                visible: !searchInput.text && !searchInput.activeFocus
            }
        }

        Rectangle {
            id: searchDivider
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: search.bottom
            height: 3
            color: COMMON.bg4
        }

        ThumbnailGrid {
            id: gallery
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: searchDivider.bottom
            anchors.bottom: parent.bottom
            clip: true
            model: Sql {
                id: filesSql
                query: root.asleep ? "" : ("SELECT file, width, height, parameters FROM images WHERE folder = '" + folder.currentValue + "' AND parameters LIKE '%" + search.text + "%' ORDER BY idx DESC;")
                
                property bool reset: false

                function refresh() {
                    gallery.positionViewAtBeginning()
                    gallery.setSelection(0)
                }

                onQueryChanged: {
                    filesSql.refresh()
                    reset = true
                }
                onResultsChanged: {
                    if(reset) {
                        filesSql.refresh()
                        reset = false
                    }
                    if(gallery.count != filesSql.length) {
                        console.log(gallery.count, filesSql.length)
                    }
                    gallery.applySelection()
                }
            }

            onContextMenu: {
                let files = gallery.getSelectedFiles()
                if(files.length > 0) {
                    galleryContextMenu.folder = folder.currentValue
                    galleryContextMenu.files = files
                    galleryContextMenu.popup()
                }
            }

            SContextMenu {
                id: galleryContextMenu
                width: 100

                property var files: []
                property var folder: ""

                Sql {
                    id: destinationsSql
                    query: "SELECT name, folder FROM folders WHERE folder != '" + folder.currentValue + "';"
                }

                SContextMenuItem {
                    text: root.tr("Open", "General")
                    onTriggered: {
                        GALLERY.doOpenFiles(galleryContextMenu.files)
                    }
                }

                SContextMenuItem {
                    text: root.tr("Visit", "General")
                    onTriggered: {
                        GALLERY.doVisitFiles(galleryContextMenu.files)
                    }
                }

                SContextMenuSeparator { }

                SContextMenu {
                    id: copyToMenu
                    title: root.tr("Copy to", "General")
                    width: 120
                    Instantiator {
                        model: destinationsSql
                        SContextMenuItem {
                            text: sql_name
                            onTriggered: {
                                GALLERY.doCopy(sql_folder, galleryContextMenu.files)
                            }
                        }
                        onObjectAdded: copyToMenu.insertItem(index, object)
                        onObjectRemoved: copyToMenu.removeItem(object)
                    }
                }

                SContextMenu {
                    id: moveToMenu
                    title: root.tr("Move to", "General")
                    width: 120
                    Instantiator {
                        model: destinationsSql
                        SContextMenuItem {
                            text: sql_name
                            onTriggered: {
                                GALLERY.doMove(sql_folder, galleryContextMenu.files)
                            }
                        }
                        onObjectAdded: moveToMenu.insertItem(index, object)
                        onObjectRemoved: moveToMenu.removeItem(object)
                    }
                }

                SContextMenuSeparator { }

                SContextMenuItem {
                    text: root.tr("Delete", "General")
                    onTriggered: {
                        deleteDialog.show(galleryContextMenu.files)
                    }
                }
            }

            onDrag: {
                GALLERY.doDrag(gallery.getSelectedFiles())
            }

            Connections {
                target: GALLERY
                function onCellSizeChanged() {
                    gallery.setCellSize(GALLERY.cellSize)
                }
            }
        }

    

        Rectangle {
            id: infoRight
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.left: infoRightText.left
            anchors.rightMargin: -5
            anchors.bottomMargin: -5
            opacity: 0.9
            height: 25
            visible: infoRightText.text != ""
            color: "#e0101010"
            border.width: 1
            border.color: COMMON.bg3
        }

        SText {
            id: infoRightText
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            verticalAlignment: Text.AlignVCenter
            rightPadding: 8
            leftPadding: 8
            topPadding: 8
            bottomPadding: 1
            font.pointSize: 9
            text: root.tr("%1 images").arg(gallery.count)
        }

        Rectangle {
            id: infoLeft
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.right: infoLeftText.right
            anchors.leftMargin: -5
            anchors.bottomMargin: -5
            opacity: 0.9
            height: 25
            visible: infoLeftText.text != ""
            color: "#e0101010"
            border.width: 1
            border.color: COMMON.bg3
        }

        SText {
            id: infoLeftText
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            verticalAlignment: Text.AlignVCenter
            rightPadding: 8
            leftPadding: 8
            topPadding: 8
            bottomPadding: 1
            font.pointSize: 9
            text: gallery.selectedLength > 1 ? root.tr("%1 images selected").arg(gallery.selectedLength)  : ""
        }
    }

    Item {
        anchors.right: galleryDivider.left
        anchors.top: parent.top
        width: Math.max(200, galleryDivider.x)
        height: Math.max(200, parent.height)

        SShadow {
            anchors.fill: view
        }

        MovableImage {
            id: view

            source: gallery.currentSource
            sourceWidth: gallery.currentWidth
            sourceHeight: gallery.currentHeight

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: imageDivider.top
            height: Math.max(200, imageDivider.y)   
        }

        Rectangle {
            id: sizeInfo
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.left: sizeInfoText.left
            anchors.topMargin: -5
            opacity: 0.8
            height: 25
            visible: sizeInfoText.visible
            color: "#c0101010"
            border.width: 1
            border.color: COMMON.bg3
        }

        SText {
            id: sizeInfoText
            visible: text != ""
            anchors.top: parent.top
            anchors.right: parent.right
            verticalAlignment: Text.AlignVCenter
            rightPadding: 8
            leftPadding: 8
            topPadding: 1
            bottomPadding: 8
            font.pointSize: 9
            color: COMMON.fg1_5
            text: gallery.currentWidth != 0 ? gallery.currentWidth + "x" + gallery.currentHeight : ""
        }

        Rectangle {
            anchors.fill: metadata
            anchors.margins: -5
            color: COMMON.bg0
        }

        Rectangle {
            id: metadata
            anchors.right: parent.right
            anchors.top: imageDivider.bottom
            width: Math.max(200, parent.width - 10)
            height: Math.max(100, parent.height - (imageDivider.y + 5) - 10)
            anchors.margins: 5
            border.width: 1
            border.color: COMMON.bg4
            color: "transparent"
            clip: true

            Rectangle {
                id: headerParams
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 25
                border.width: 1
                border.color: COMMON.bg4
                color: COMMON.bg3
                SText {
                    anchors.fill: parent
                    text: root.tr("Parameters")
                    color: COMMON.fg1_5
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: inspectButton.left
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: root.tr("Import")
                    icon: "qrc:/icons/back.svg"
                    inset: 8
                    onPressed: {
                        GUI.currentTab = "Generate"
                        BASIC.importImage(gallery.currentSource)
                    }
                }

                SIconButton {
                    id: inspectButton
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: root.tr("Inspect")
                    icon: "qrc:/icons/search.svg"
                    inset: 8
                    onPressed: {
                        GUI.currentTab = "Generate"
                        BASIC.pasteText(gallery.currentParams)
                    }
                }
            }

            STextArea {
                id: parameters
                color: COMMON.bg1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: headerParams.bottom
                anchors.bottom: parent.bottom
                anchors.margins: 1

                readOnly: true

                text: gallery.currentParams

                Component.onCompleted: {
                    GUI.setHighlighting(parameters.area.textDocument)
                }
            }
        }

        SDividerHB {
            id: imageDivider
            anchors.left: parent.left
            anchors.right: parent.right
            minOffset: 5
            maxOffset: parent.height
            offset: 175
        }
    }

    SDividerVR {
        id: galleryDivider
        minOffset: 5
        maxOffset: parent.width
        offset: 600
    }

    Keys.onPressed: {
        event.accepted = true
        const prev = gallery.currentIndex
        switch(event.key) {
        case Qt.Key_Up:
            gallery.moveUp(event.modifiers)
            break;
        case Qt.Key_Down:
            gallery.moveDown(event.modifiers)
            break;
        case Qt.Key_Left:
            gallery.moveLeft(event.modifiers)
            break;
        case Qt.Key_Right:
            gallery.moveRight(event.modifiers)
            break;
        case Qt.Key_Escape:
            if(searchInput.activeFocus) {
                search.text = ""
                searchInput.text = ""
                root.releaseFocus()
            }
            break;
        default:
            event.accepted = false
            break;
        }
        if (event.accepted) {
            if(prev != gallery.currentIndex) {
                view.thumbnailOnly = event.isAutoRepeat
            }
            return
        }

        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_C:
                var selected = gallery.getSelectedFiles()
                if(gallery.currentSource != null) {
                    GALLERY.doClipboard(gallery.getSelectedFiles())
                }
                break;
            case Qt.Key_Minus:
                GALLERY.adjustCellSize(-50)
                break;
            case Qt.Key_Equal:
                GALLERY.adjustCellSize(50)
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
    Keys.onReleased: {
        switch(event.key) {
            case Qt.Key_Delete:
                deleteDialog.show(gallery.getSelectedFiles())
                break;
            case Qt.Key_Up:
            case Qt.Key_Down:
            case Qt.Key_Left:
            case Qt.Key_Right:
                if (!event.isAutoRepeat) {
                    view.thumbnailOnly = false
                }
                break;
            default:
                event.accepted = false
                break;
        }
    }
}