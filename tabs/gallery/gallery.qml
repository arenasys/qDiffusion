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

    Rectangle {
        id: galleryDivider
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 5
        property int minX: 5
        property int maxX: parent.width
        property int offset: 600
        x: parent.width - offset
        color: COMMON.bg4

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onPositionChanged: {
                if(pressedButtons) {
                    galleryDivider.offset = Math.min(galleryDivider.maxX, Math.max(galleryDivider.minX, root.width - (galleryDivider.x + mouseX)))
                }
            }
        }

        onMaxXChanged: {
            if(parent.width > 0 && galleryDivider.x > 0)
                galleryDivider.offset = Math.min(galleryDivider.maxX, Math.max(galleryDivider.minX, galleryDivider.offset))
        }
    }

    Rectangle {
        id: imageDivider
        anchors.left: parent.left
        anchors.right: galleryDivider.left
        height: 5
        property int minY: 5
        property int maxY: parent.height
        property int offset: 150
        y: parent.height - offset
        color: COMMON.bg4

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onPositionChanged: {
                if(pressedButtons) {
                    imageDivider.offset = Math.min(imageDivider.maxY, Math.max(imageDivider.minY, root.height - (imageDivider.y + mouseY)))
                }
            }
        }

        onMaxYChanged: {
            if(parent.height > 0 && imageDivider.y > 0)
                imageDivider.offset = Math.min(imageDivider.maxY, Math.max(imageDivider.minY, imageDivider.offset))
        }
    }

    Media {
        id: view
        
        color: COMMON.bg0
        
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
        height: 5
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
            query: "SELECT file, width, height, parameters FROM images WHERE folder = '" + folder.currentValue + "' AND parameters LIKE '%" + search.text + "%' ORDER BY file;"
            onResultsChanged: {
                gallery.currentIndex = 0
            }
        }
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

    MouseArea {
        visible: searchInput.activeFocus
        anchors.fill: parent
        onClicked: {
            root.releaseFocus()
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
        width: 5
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
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            case Qt.Key_Up:
                gallery.moveCurrentIndexUp()
                break;
            case Qt.Key_Down:
                gallery.moveCurrentIndexDown()
                break;
            case Qt.Key_Left:
                gallery.moveCurrentIndexLeft()
                break;
            case Qt.Key_Right:
                gallery.moveCurrentIndexRight()
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }
}