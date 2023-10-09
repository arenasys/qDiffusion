import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import "../../style"
import "../../components"

GridView {
    id: thumbView

    property var currentSource: currentItem != null ? currentItem.source : null
    property var currentWidth: currentItem != null ? currentItem.sourceWidth : 0
    property var currentHeight: currentItem != null ? currentItem.sourceHeight : 0
    property var currentParams: currentItem != null ? currentItem.sourceParams : ""

    property int cellSize: 200
    property int padding: 10
    property int fixedIndex: -1
    cellWidth: Math.max((thumbView.width-padding)/Math.max(Math.ceil(thumbView.width/cellSize), 1), 50)
    cellHeight: cellWidth
    
    function setCellSize(size) {
        // force the layout to keep the top left item in view when resizing
        fixedIndex = indexAt(contentX, contentY)
        cellSize = size        
    }

    onContentHeightChanged: {
        // try to pinpoint the moment when the resize has completed
        let idx = indexAt(contentX + width/2, contentY + height/2)
        let cnt = Math.floor((contentHeight*width)/(cellWidth*cellHeight))
        if(fixedIndex != -1 && idx != -1 && cnt >= count) {
            positionViewAtIndex(fixedIndex, GridView.Beginning)
            fixedIndex = -1
        }
    }

    property var selected: []
    property var selectedLength: 1
    
    function getFile(idx) {
        var record = thumbView.model.get(idx)
        if(record == null) {
            return null
        } else {
            return record["file"]
        }
    }

    function getIndex(file) {
        for(var i = 0; i < thumbView.model.length; i++) {
            if(thumbView.model.get(i)["file"] == file) {
                return i
            }
        }
        return -1
    }

    function getSelectedFiles() {
        var current = getFile(currentIndex)
        var pos = selected.indexOf(current)
        if(pos == -1) {
            selected.push(current)
        }
        return selected
    }

    function addToSelected(index) {
        var id = getFile(index)
        removeFromSelected(index)
        selected.push(id)
        selectedLength = selected.length
    }

    function removeFromSelected(index) {
        var id = getFile(index)
        var pos = selected.indexOf(id)
        if(pos !== -1) {
            selected.splice(pos, 1)
        }
        selectedLength = selected.length
    }

    function setSelection(index) {
        var id = getFile(index)
        thumbView.currentIndex = index
        thumbView.selected = [id]
        thumbView.selectedLength = 1
    }

    function addSelectionRange(start, end) {
        let delta = end < start ? -1 : 1
        for(let i = start; i != end; i += delta) {
            addToSelected(i)
        }
        addToSelected(end)
    }

    function clearSelection() {
        thumbView.currentIndex = 0
        thumbView.selected = []
        thumbView.selectedLength = 1
    }

    function applySelection() {
        if(thumbView.model.length == 0) {
            selected = []
            selectedLength = 0
            return;
        }

        var remaining = []
        for(var i = 0; i < selected.length; i++) {
            if(getIndex(selected[i]) != -1) {
                remaining.push(selected[i])
            }
        }
        selected = remaining
        selectedLength = remaining.length

        var currentID = getFile(currentIndex)

        if(selectedLength > 0 && !selected.includes(currentID)) {
            var idx = getIndex(selected[0])
            if(idx != -1) {
                currentIndex = idx
            } else {
                selected = [getFile(currentIndex)]
                selectedLength = 1
            }
        }
    }

    function movedSelection(modifiers, prev, curr) {
        if(modifiers & Qt.ControlModifier) {
            addToSelected(curr)
            applySelection()
        } else if(modifiers & Qt.ShiftModifier) {
            addSelectionRange(prev, curr)
            applySelection()
        } else {
            selected = [getFile(curr)]
            applySelection()
        }
    }

    function moveUp(modifiers) {
        let prev = currentIndex
        moveCurrentIndexUp()
        movedSelection(modifiers, prev, currentIndex)
    }

    function moveDown(modifiers) {
        let prev = currentIndex
        moveCurrentIndexDown()
        movedSelection(modifiers, prev, currentIndex)
    }

    function moveLeft(modifiers) {
        let prev = currentIndex
        moveCurrentIndexLeft()
        movedSelection(modifiers, prev, currentIndex)
    }

    function moveRight(modifiers) {
        let prev = currentIndex
        moveCurrentIndexRight()
        movedSelection(modifiers, prev, currentIndex)
    }

    signal contextMenu()
    signal drag()

    interactive: false
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: SScrollBarV {
        id: scrollBar
        stepSize: 1/Math.ceil(thumbView.count / Math.round(thumbView.width/thumbView.cellWidth))
        policy: thumbView.contentHeight > thumbView.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
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

    footer: Item {
        width: 10
        height: 10
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

        selected: thumbView.currentIndex === index || (thumbView.selectedLength <= 0 ? false : thumbView.selected.includes(sql_file))

        onSelect: {
            if(!selected) {
                thumbView.setSelection(index)
            }
        }

        onControlSelect: {
            if(thumb.selected){
                thumbView.removeFromSelected(index)
                thumbView.applySelection()
            } else {
                thumbView.addToSelected(index)
                thumbView.applySelection()
            }
        }

        onShiftSelect: {
            thumbView.selected = []
            thumbView.addSelectionRange(thumbView.currentIndex, index)
            thumbView.applySelection()
        }

        onContextMenu: {
            if(!thumbView.selected.includes(sql_file)) {
                thumbView.setSelection(index)
            }
            thumbView.contextMenu()
        }

        onOpen: {
            thumbView.setSelection(index)
        }

        onDrag: {
            thumbView.drag()
        }
    }
}