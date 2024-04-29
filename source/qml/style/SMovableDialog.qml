import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"
import "../components"

Item {
    id: dialog

    visible: false

    signal opened()
    signal accepted()
    signal rejected()
    signal applied()

    function open() {
        visible = true
        dialog.opened()
    }

    function apply() {
        dialog.applied()
    }

    function accept() {
        dialog.setDim(false)
        dialog.accepted()
        dialog.visible = false
    }

    function reject() {
        dialog.setDim(false)
        dialog.rejected()
        dialog.visible = false
    }

    property alias contentItem: content.data
    property alias titleItem: titleExtra.data
    property alias backgroundItem: backgroundExtra.data

    property var anchored: true
    property var centered: true

    property var inverseX: true
    property var inverseY: true
    property var offsetX: 0
    property var offsetY: 0

    property var minWidth: 0
    property var minHeight: 0
    property var usualWidth: minWidth
    property var usualHeight: minHeight

    width: usualWidth
    height: usualHeight + footer.height

    property var fakeHeight: usualHeight + 35
    property var fakeWidth: width

    function setPosition(x, y) {
        inverseX = x + (fakeWidth/2) > parent.width / 2
        inverseY = y + (fakeHeight/2) > parent.height / 2

        offsetX = inverseX ? parent.width - x - fakeWidth : x
        offsetY = inverseY ? parent.height - y - fakeHeight : y
    }

    function setAnchored(anchored) {
        if(!anchored) {
            dialog.setPosition(dialog.x, dialog.y)
        } else {
            centered = true
        }
        dialog.anchored = anchored
    }
    
    x: anchored ? (parent.width - fakeWidth)/2 : (inverseX ? parent.width - offsetX - fakeWidth : offsetX)
    y: anchored ? (parent.height - fakeHeight)/2 : (inverseY ? parent.height - offsetY - fakeHeight : offsetY)

    property var dim: false

    function setDim(newDim) {
        if(newDim == dim) {
            return
        }

        if(newDim) {
            dialog.parent = COMMON.overlay
        } else {
            var p = dialog.parent.mapToItem(dialog.originalParent, dialog.x, dialog.y)
            dialog.parent = dialog.originalParent
            dialog.setPosition(p.x, p.y)
        }
        
        dim = newDim
    }

    onAnchoredChanged: {
        setDim(anchored)
    }

    Component.onDestruction: {
        setDim(false)
    }
    
    property var originalParent: null

    Component.onCompleted: {
        originalParent = parent
    }

    property var standardButtons: Dialog.Ok

    property var title: root.tr("Dialog")

    function tr(str, file = "SMovableDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    onOpened: {
        enterItem.forceActiveFocus()
    }

    Item {
        id: enterItem
        Keys.onPressed: {
            event.accepted = true
            switch(event.key) {
            case Qt.Key_Enter:
            case Qt.Key_Return:
                dialog.accept()
                break;
            default:
                event.accepted = false
                break;
            }
        }
    }

    Item {
        id: background
        anchors.fill: parent
        RectangularGlow {
            anchors.fill: bg
            glowRadius: 5
            opacity: 0.75
            spread: 0.2
            color: "black"
            cornerRadius: 10
        }

        Rectangle {
            id: bg
            anchors.fill: parent
            anchors.margins: -1
            color: COMMON.bg1
            border.width: 1
            border.color: COMMON.bg4
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg0
        }

        MouseArea {
            anchors.fill: parent
        }

        Item {
            id: backgroundExtra
            anchors.fill: parent
        }
    }

    Item {
        id: content
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        anchors.leftMargin: 5
        anchors.rightMargin: 5
    }

    Item {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 20
        MouseArea {
            id: titleArea
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            cursorShape: Qt.SizeAllCursor

            property var offset: Qt.point(0, 0)

            function getPosition() {
                return titleArea.mapToItem(dialog.parent, mouseX, mouseY)
            }

            function getCenter() {
                return Qt.point((dialog.parent.width - dialog.fakeWidth) / 2, (dialog.parent.height - dialog.fakeHeight) / 2)
            }

            onPressed: {
                var pos = getPosition()
                offset = Qt.point(pos.x - dialog.x, pos.y - dialog.y)
            }

            onPositionChanged: {
                var pos = getPosition()

                if(dialog.anchored) {
                    var original = Qt.point(offset.x + dialog.x, offset.y + dialog.y)
                    var delta = Qt.point(pos.x - original.x, pos.y - original.y)
                    if(Math.abs(delta.x) > 50 || Math.abs(delta.y) > 50) {
                        dialog.setAnchored(false)
                    }
                }

                if(!dialog.anchored) {
                    var x = Math.max(0, Math.min(dialog.parent.width - dialog.width, pos.x - offset.x))
                    var y = Math.max(0, Math.min(dialog.parent.height - dialog.height, pos.y - offset.y))

                    dialog.setPosition(x, y)
                }
            }
        }

        SText {
            color: COMMON.fg2
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: dialog.title
            pointSize: 9
            font.bold: true
        }

        Item {
            id: titleExtra
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        SIconButton {
            id: closeButton
            visible: !dialog.anchored
            color: "transparent"
            icon: "qrc:/icons/cross.svg"
            anchors.top: parent.top
            anchors.right: parent.right
            height: 20
            width: visible ? 20 : 0
            inset: 6

            onPressed: {
                dialog.reject()
            }
        }
    }

    //spacing: 0
    //verticalPadding: 0

    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: dialog.standardButtons == 0 ? 5 : 35
        color: COMMON.bg1
        DialogButtonBox {
            anchors.centerIn: parent
            standardButtons: dialog.standardButtons
            alignment: Qt.AlignHCenter
            spacing: 5

            background: Item {
                implicitHeight: 25
            }

            delegate: Button {
                id: control
                implicitHeight: 25

                contentItem: SText {
                    id: contentText
                    color: COMMON.fg1
                    text: control.text
                    pointSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 0
                    color: control.down ? COMMON.bg5 : COMMON.bg4
                    border.color: COMMON.bg6
                }
            }

            onApplied: dialog.apply()
            onAccepted: dialog.accept()
            onRejected: dialog.reject()
        }
    }

    Item {
        visible: !dialog.anchored
        anchors.fill: parent
        clip: true

        Rectangle {
            id: expandMarker
            color: COMMON.bg4
            width: 10
            height: 10
            rotation: 45
            x: dialog.inverseX ? -5 : parent.width - 5
            y: parent.height - 5
        }
    }

    MouseArea {
        visible: !dialog.anchored
        id: expandArea
        
        x: expandMarker.x
        y: expandMarker.y
        width: 10
        height: 10

        cursorShape: dialog.inverseX ? Qt.SizeBDiagCursor : Qt.SizeFDiagCursor

        property var startSize: Qt.point(0, 0)
        property var startPos: Qt.point(0, 0)

        function getPosition() {
            return expandArea.mapToItem(dialog.parent, mouseX, mouseY)
        }

        onPressed: {
            startSize = Qt.point(dialog.usualWidth, dialog.usualHeight)
            startPos = getPosition()
        }

        onPositionChanged: {
            var pos = getPosition()
            var delta = Qt.point(pos.x - startPos.x, pos.y - startPos.y)

            dialog.usualWidth = Math.max(dialog.minWidth, startSize.x + (dialog.inverseX ? -delta.x : delta.x))
            dialog.usualHeight = Math.max(dialog.minHeight, startSize.y + delta.y)
        }
    }
}