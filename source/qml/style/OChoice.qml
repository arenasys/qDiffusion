import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: root
    property var label: "Label"
    property var tooltip: ""
    property alias model: control.model
    property var mini: height == 20
    property var value: control.model.length == 0 ? "" : control.model[control.currentIndex]
    property alias currentIndex: control.currentIndex
    property var disabled: false
    property var overlay: root.disabled
    property var padded: true

    property alias control: control
    property alias delegate: control.delegate

    property variant bindMap: null
    property var bindKeyCurrent: null
    property var bindKeyModel: null

    property alias popupHeight: control.popupHeight

    function decoration(value) {
        return ""
    }

    function display(text) {
        return text
    }

    Connections {
        target: bindMap
        function onUpdated() {
            var m = root.bindMap.get(root.bindKeyModel);
            var c = root.bindMap.get(root.bindKeyCurrent);
            if(m != root.model) {
                root.model = m;
            }
            root.currentIndex = root.model.indexOf(c);
        }
    }

    Component.onCompleted: {
        if(root.bindMap != null && root.bindKeyCurrent != null && root.bindKeyModel != null) {
            var m = root.bindMap.get(root.bindKeyModel);
            var c = root.bindMap.get(root.bindKeyCurrent);
            root.model = m;
            root.currentIndex = m.indexOf(c);
        }
    }

    onCurrentIndexChanged: {
        if(root.bindMap != null && root.bindKeyCurrent != null && root.bindKeyModel != null) {
            var m = root.bindMap.get(root.bindKeyModel);
            root.bindMap.set(root.bindKeyCurrent, m[root.currentIndex]);
        }
    }

    signal tryEnter()
    signal enter()
    signal exit()
    signal contextMenu()
    signal selected()

    SToolTip {
        id: infoToolTip
        visible: !control.popup.opened && !disabled && tooltip != "" && mouseArea.containsMouse
        delay: 200
        text: root.tooltip != undefined ? root.tooltip : ""
    }

    ComboBox {
        id: control
        anchors.fill: parent
        anchors.margins: root.padded ? 2 : 0
        anchors.bottomMargin: 0
        focusPolicy: Qt.NoFocus

        property var popupHeight: 300

        function selected() {
            root.selected()
        }

        delegate: Rectangle {
            width: control.popup.width
            height: 22
            color: delegateMouse.containsMouse ?  COMMON.bg4 : COMMON.bg3
            SText {
                id: decoText
                anchors.right: parent.right
                width: contentWidth
                height: 22
                text: root.decoration(modelData)
                color: width < contentWidth ? "transparent" : COMMON.fg2
                font.pointSize:  8.5
                rightPadding: 8
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            SText {
                id: valueText
                anchors.left: parent.left
                anchors.right: decoText.left

                height: 22
                text: root.display(modelData)
                color: COMMON.fg0
                font.pointSize:  8.5
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
                    control.currentIndex = index
                    control.selected()
                    control.popup.close()
                }
            }
        }

        indicator: Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 10
            color: COMMON.bg4
            Canvas {
                id: canvas
                anchors.fill: parent
                contextType: "2d"

                Connections {
                    target: control.popup
                    function onVisibleChanged() { canvas.requestPaint(); }
                }

                onPaint: {
                    var context = getContext("2d");
                    var ox = width/2
                    var oy = height/2
                    var dx = root.mini ? 2.5 : 3.25
                    var dy = control.popup.visible ? -dx : dx

                    context.reset();
                    context.moveTo(ox-dx, oy-dy);
                    context.lineTo(ox+dx, oy-dy);
                    context.lineTo(ox, oy+dy);
                    context.closePath();
                    context.fillStyle = COMMON.bg6;
                    context.fill();
                }
            }
        }

        contentItem: Item {
            SText {
                id: labelText
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                leftPadding: 5
                text: root.label
                font.pointSize: root.mini ? 7.85 : COMMON.pointLabel
                color: COMMON.fg1_5
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                monospace: false
            }
            
            SText {
                anchors.right: parent.right
                anchors.left: labelText.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                leftPadding: 5
                rightPadding: 7

                text: root.display(control.displayText)
                font.pointSize: root.mini ? 7.7 : COMMON.pointValue
                color: COMMON.fg0
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }

        background: Rectangle {
            implicitWidth: 120
            implicitHeight: 30
            color: COMMON.bg2_5
            border.color: COMMON.bg4
        }

        popup: Popup {
            y: control.height
            width: Math.max(100, control.width)
            implicitHeight: Math.min(control.popupHeight, contentItem.implicitHeight+2)
            padding: 2

            onOpenedChanged: {
                if(opened) {
                    root.enter()
                } else {
                    root.exit()
                }
            }

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                boundsBehavior: Flickable.StopAtBounds
                ScrollIndicator.vertical: ScrollIndicator {
                    anchors.right: parent.right
                    anchors.rightMargin: -2
                }
            }

            background: Rectangle {
                color: COMMON.bg0
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    color: COMMON.bg4
                }
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if(mouse.button == Qt.RightButton) {
                root.contextMenu()
            } else {
                root.forceActiveFocus()
                root.tryEnter()
                if(control.popup.opened) {
                    control.popup.close()
                } else if (!root.disabled) {
                    control.popup.open()
                }
            }
        }
    }

    Rectangle {
        anchors.fill: control
        visible: root.overlay
        color: "#90101010"
    }

    Rectangle {
        anchors.fill: control
        visible: root.disabled
        color: "#c0101010"
    }
    
    Keys.onPressed: {
        event.accepted = true
        switch(event.key) {
        case Qt.Key_Up:
            if(control.currentIndex > 0) {
                control.currentIndex -= 1
            }
            break;
        case Qt.Key_Down:
            if(control.currentIndex < control.count-1) {
                control.currentIndex += 1
            }
            break;
        case Qt.Key_Return:
            control.popup.close()
        default:
            event.accepted = false
            break;
        }
    }
}