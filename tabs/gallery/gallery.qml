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
        property int offset: 200
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
        
        source: sources.currentSource
        sourceWidth: sources.currentWidth
        sourceHeight: sources.currentHeight

        anchors.left: parent.left
        anchors.right: galleryDivider.left
        anchors.top: parent.top
        anchors.bottom: imageDivider.top        
    }

    ThumbnailGrid {
        id: sources
        anchors.left: galleryDivider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        model: Sql {
            id: sql
            query: "SELECT file, width, height FROM images ORDER BY file;"
        }
    }

}