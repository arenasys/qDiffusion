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
            query: "SELECT file, width, height, parameters FROM images WHERE folder = '" + folder.currentValue + "' AND parameters LIKE '%" + search.text + "%' ORDER BY file;"
            
            property bool reset: false
            onQueryChanged: {
                gallery.positionViewAtBeginning()
                reset = true
            }
            onResultsChanged: {
                if(reset) {
                    gallery.clearSelection()
                    reset = false
                }
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
                title: "Copy to"
                SContextMenuItem {
                    text: "Clipboard"
                }
                Repeater {
                    model: destinationsSql
                    SContextMenuItem {
                        text: sql_name
                        onTriggered: {
                            GALLERY.doCopy(sql_folder, galleryContextMenu.files)
                        }
                    }
                }
            }

            SContextMenu {
                title: "Move to"
                Repeater {
                    model: destinationsSql
                    SContextMenuItem {
                        text: sql_name
                        onTriggered: {
                            GALLERY.doMove(sql_folder, galleryContextMenu.files)
                        }
                    }
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
        radius: 5
        color: COMMON.bg1
        opacity: 0.9
        height: 25
        visible: infoRightText.text != ""
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
        radius: 5
        color: COMMON.bg1
        opacity: 0.9
        height: 25
        visible: infoLeftText.text != ""
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
        offset: 150
    }

    Rectangle {
        id: metadata
        anchors.left: parent.left
        anchors.right: galleryDivider.left
        anchors.top: imageDivider.bottom
        anchors.bottom: parent.bottom
        color: COMMON.bg1

        Rectangle {
            id: parameters
            anchors.fill: parent
            anchors.margins: 10
            color: COMMON.bg3

            ScrollView {
                anchors.fill: parent
                contentWidth: width
                clip: true
                STextSelectable {
                    width: parameters.width
                    padding: 5
                    wrapMode: Text.WordWrap
                    text: gallery.currentParams
                    color: COMMON.fg1
                }
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