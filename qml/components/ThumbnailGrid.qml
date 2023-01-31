import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

GridView {
    id: thumbView

    property var currentSource: currentItem != null ? currentItem.source : null
    property var currentWidth: currentItem != null ? currentItem.sourceWidth : 0
    property var currentHeight: currentItem != null ? currentItem.sourceHeight : 0
    property var currentParams: currentItem != null ? currentItem.sourceParams : ""

    property int cellSize: 250
    property int padding: 10

    signal open()
    signal contextMenu()

    function align() {
        thumbView.positionViewAtIndex(thumbView.currentIndex, GridView.Contain)
    }

    interactive: false
    boundsBehavior: Flickable.StopAtBounds
    
    cellWidth: Math.max((thumbView.width-padding)/Math.max(Math.ceil(thumbView.width/cellSize), 1), 100)
    cellHeight: cellWidth

    ScrollBar.vertical: ScrollBar {
        id: scrollBar
        stepSize: 1/Math.ceil(thumbView.count / Math.round(thumbView.width/thumbView.cellWidth))
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: {
            if(wheel.angleDelta.y < 0) {
                scrollBar.increase()
            } else {
                scrollBar.decrease()
            }
        }
    }

    delegate: Thumbnail {
        id: thumb
        width: cellWidth
        height: cellHeight
        padding: thumbView.padding
        
        property int sourceWidth: sql_width
        property int sourceHeight: sql_height
        property var sourceParams: sql_parameters
        source: sql_file

        property var thumb_index: index

        selected: thumbView.currentIndex === thumb_index

        onSelect: {
            thumbView.currentIndex = index
        }

        onContextMenu: {
            thumbView.contextMenu()
        }

        onOpen: {
            thumbView.open()
        }
    }
}