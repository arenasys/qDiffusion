import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

GridView {
    id: thumbView

    property int cellSize: 250
    property int padding: 10

    signal open()
    signal contextMenu()

    function align() {
        thumbView.positionViewAtIndex(thumbView.currentIndex, GridView.Contain)
    }

    onWidthChanged: align()

    cellWidth: (thumbView.width-padding)/Math.max(Math.ceil(thumbView.width/cellSize), 1)
    cellHeight: cellWidth
    topMargin: padding
    leftMargin: padding

    ScrollBar.vertical: ScrollBar {    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: {
            if(wheel.angleDelta.y < 0) {
                thumbView.moveCurrentIndexDown()
            } else {
                thumbView.moveCurrentIndexUp()
            }
        }
    }

    delegate: Thumbnail {
        id: thumb
        width: cellWidth-padding
        height: cellHeight-padding

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