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

    function releaseFocus() {
        parent.releaseFocus()
    }

    SShadow {
        anchors.fill: view
    }

    MovableImage {
        id: view

        source: gallery.currentSource
        sourceWidth: gallery.currentWidth
        sourceHeight: gallery.currentHeight

        anchors.left: parent.left
        anchors.right: galleryDivider.left
        anchors.top: parent.top
        anchors.bottom: imageDivider.top        
    }

    
    Rectangle {
        id: searchDivider
        anchors.left: galleryDivider.right
        anchors.right: parent.right
        anchors.top: search.bottom
        height: 3
        color: COMMON.bg4
    }

    ThumbnailGrid {
        id: gallery
        anchors.left: galleryDivider.right
        anchors.right: parent.right
        anchors.top: searchDivider.bottom
        anchors.bottom: parent.bottom
        clip: true
        model: Sql {
            id: filesSql
            query: "SELECT file, width, height, parameters FROM images WHERE folder = '" + folder.currentValue + "' AND parameters LIKE '%" + search.text + "%' ORDER BY file DESC;"
            
            property bool reset: false

            function refresh() {
                gallery.positionViewAtBeginning()
                gallery.setSelection(0)
            }

            onQueryChanged: {
                filesSql.refresh()
                reset = true
            }
            onBigChange: {
                filesSql.forceReset()
                filesSql.refresh()
            }
            onResultsChanged: {
                if(reset) {
                    filesSql.refresh()
                    reset = false
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
                text: "Open"
                onTriggered: {
                    GALLERY.doOpenImage(galleryContextMenu.files)
                }
            }

            SContextMenuItem {
                text: "Visit"
                onTriggered: {
                    GALLERY.doOpenFolder(galleryContextMenu.files)
                }
            }

            SContextMenuSeparator { }

            SContextMenu {
                id: copyToMenu
                title: "Copy to"
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
                title: "Move to"
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
                text: "Delete"
                onTriggered: {
                    dialog.open()
                }
            }
        }

        onDrag: {
            GALLERY.doDrag(gallery.getSelectedFiles())
        }
    }

    SDialog {
        id: dialog
        title: "Confirmation"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true

        height: 120

        SText {
            anchors.fill: parent
            padding: 5
            text: "Delete " + galleryContextMenu.files.length + " images?"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        onAccepted: {
            GALLERY.doDelete(galleryContextMenu.files)
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
        text: gallery.count + " images"
    }

    Rectangle {
        id: infoLeft
        anchors.left: galleryDivider.right
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
        anchors.left: galleryDivider.right
        verticalAlignment: Text.AlignVCenter
        rightPadding: 8
        leftPadding: 8
        topPadding: 8
        bottomPadding: 1
        font.pointSize: 9
        text: gallery.selectedLength > 1 ? gallery.selectedLength + " images selected"  : ""
    }

    SDividerVR {
        id: galleryDivider
        minOffset: 5
        maxOffset: parent.width
        offset: 600
    }

    SDividerHB {
        id: imageDivider
        anchors.left: parent.left
        anchors.right: galleryDivider.left
        minOffset: 5
        maxOffset: parent.height
        offset: 175
    }

    Rectangle {
    id: metadata
        anchors.left: parent.left
        anchors.right: galleryDivider.left
        anchors.top: imageDivider.bottom
        anchors.bottom: parent.bottom
        anchors.margins: 5
        border.width: 1
        border.color: COMMON.bg4
        color: "transparent"

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
                text: "Parameters"
                color: COMMON.fg1_5
                leftPadding: 5
                verticalAlignment: Text.AlignVCenter
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
        anchors.left: galleryDivider.right
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
            text: "Search..."
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
                gallery.setCellSize(100)
                break;
            case Qt.Key_Equal:
                gallery.setCellSize(200)
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