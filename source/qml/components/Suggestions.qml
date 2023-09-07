import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"
import "../components"

Item {
    id: root
    width: 200

    property var target
    property var suggestions

    property var area: target.area

    property var flip: false

    property var text: area.text
    property var position: area.cursorPosition
    property var active: list.visible
    property var typed: false

    property var targetStart: null
    property var targetEnd: null
    property var replace: false

    function update() {
        if(root.typed) {
            root.suggestions.updateSuggestions(root.text, root.position, false)
            root.targetStart = root.suggestions.start(root.text, root.position)
            root.targetEnd = root.suggestions.end(root.text, root.position)
        }
    }

    function reset() {
        root.typed = false
    }

    function complete(text) {
        target.completeText(text, root.targetStart, root.replace ? root.targetEnd : root.position)
        root.reset()
    }

    onTextChanged: {
        if(root.text == null) {
            root.reset()
        } else if (root.typed) {
            root.update()
        }
    }

    onPositionChanged: {
        update()
    }

    Connections {
        target: root.target
        function onInput(key) {
            if(key == Qt.Key_Right || key == Qt.Key_Left) {
                if (root.typed) {
                    root.update()
                }
            } else if(key != Qt.Key_Down && key != Qt.Key_Right) {
                if(!root.typed)  {
                    root.replace = root.suggestions.replace(root.text, root.position)
                }
                root.typed = true
            }
        }

        function onMenu(dir) {
            if(root.active) {
                if(dir == 0) {
                    root.typed = false
                } else {
                    list.move(dir)
                }
            }
        }

        function onTab() {
            if(root.active) {
                root.complete(list.currentItem.text)
            }
        }
    }

    Rectangle {
        visible: list.visible
        anchors.fill: list
        color: COMMON.bg2
        border.width: 1
        border.color: COMMON.bg4
        anchors.margins: -1
    }
    Rectangle {
        visible: list.visible
        anchors.fill: list
        color: "transparent"
        border.width: 1
        border.color: COMMON.bg0
        anchors.margins: -2
    }

    ListView {
        id: list
        visible: root.typed && suggestions.results.length != 0
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: root.flip ? parent.top : undefined
        anchors.top: root.flip ? undefined : parent.bottom
        anchors.topMargin: 3
        anchors.bottomMargin: 3
        height: Math.min(suggestions.results.length, 3)*20
        clip: true
        model: suggestions.results

        verticalLayoutDirection: root.flip ? ListView.BottomToTop : ListView.TopToBottom
        boundsBehavior: Flickable.StopAtBounds
        highlightFollowsCurrentItem: false

        function move(dir) {
            dir *= root.flip ? -1 : 1
            if(dir == 1) {
                decrementCurrentIndex()
            } else if (dir == -1) {
                incrementCurrentIndex()
            }
            positionViewAtIndex(currentIndex, ListView.Contain)
        }

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
            padding: 0
            barWidth: 2
            stepSize: 1/(suggestions.results.length)
            policy: list.contentHeight > list.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }

        delegate: Rectangle {
            width: list.width
            height: 20
            property var selected: list.currentIndex == index
            property var text: root.suggestions.completion(modelData, root.position-root.targetStart)
            color: selected ? COMMON.bg4 : (delegateMouse.containsMouse ? COMMON.bg3_5 : COMMON.bg3)

            SText {
                id: decoText
                anchors.right: parent.right
                width: contentWidth
                height: 20
                text: root.suggestions.detail(modelData)
                color: width < contentWidth ? "transparent" : COMMON.fg2
                font.pointSize: 8.5
                rightPadding: 8
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            SText {
                id: valueText
                anchors.left: parent.left
                anchors.right: decoText.left

                height: 20
                text: root.suggestions.display(modelData)
                color: root.suggestions.color(modelData)
                font.pointSize: 8.5
                leftPadding: 5
                rightPadding: 10
                elide: Text.ElideRight

                verticalAlignment: Text.AlignVCenter
            }
            MouseArea {
                id: delegateMouse
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: true
                onPressed: {
                    root.complete(parent.text)
                }
            }
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
    }
}