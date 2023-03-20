import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"

Item {
    id: root
    height: 30
    property var mini: height == 20

    signal deactivate()

    property var label: "Label"
    property var type: ""

    property var tooltip: ""
    property double value: 0
    property var defaultValue: null
    property double minValue: 0
    property double maxValue: 100
    property double precValue: 0
    property double incValue: 1
    property var snapValue: null
    property var labelWidth: 70
    property var bounded: true
    property var disabled: false

    property variant bindMap: null
    property var bindKey: null

    Connections {
        target: bindMap
        function onUpdated() {
            var v = root.bindMap.get(root.bindKey)
            if(v != root.value) {
                root.value = v
            }
        }
    }

    Component.onCompleted: {
        if(root.bindMap != null && root.bindKey != null) {
            root.value = root.bindMap.get(root.bindKey)
        }

        if(root.defaultValue == null) {
            root.defaultValue = root.value;
        }
    }

    onValueChanged: {
        if(root.bindMap != null && root.bindKey != null) {
            root.bindMap.set(root.bindKey, root.value)
        }
    }

    function update(pos) {
        var value = pos*(root.maxValue-root.minValue) + root.minValue
        value = parseFloat(value.toFixed(root.precValue))

        if(root.snapValue != null) {
            value = Math.round(value/root.snapValue) * root.snapValue;
        }

        if(value != root.value) {
            root.value = value
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0

        color: COMMON.bg3
        border.color: COMMON.bg4

        MouseArea {
            id: mouseArea
            anchors.left: parent.left
            anchors.right: spinnerControls.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: -2
            anchors.leftMargin: 0
            hoverEnabled: true
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            function update() {
                root.update(Math.min(width, Math.max(0, mouseX))/width)
            }


            onPressed: {
                if (mouse.button === Qt.LeftButton) {
                    root.forceActiveFocus()
                    mouseArea.update()
                } else if (mouse.button === Qt.RightButton) {
                    root.deactivate()
                }
            }

            onPositionChanged: {
                if(pressed) {
                    mouseArea.update()
                }
            }
        }

        Rectangle {
            id: indicator
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            color: COMMON.bg5
            width: Math.min((mouseArea.width) * (root.value - root.minValue)/(root.maxValue-root.minValue), parent.width)
        }

        SToolTip {
            id: infoToolTip
            x: 0
            visible: !disabled && tooltip != "" && mouseArea.containsMouse && mouseArea.mouseX < root.width/3
            delay: 100
            text: tooltip
        }

        SText {
            id: labelText
            text: root.label
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            rightPadding: 5
            width: contentWidth+5
            verticalAlignment: Text.AlignVCenter
            font.pointSize: root.mini ? 7.85 : 9.8
            color: COMMON.fg1
        }

        SText {
            id: typeText
            text: root.type
            anchors.left: labelText.right
            anchors.right: valueInput.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            rightPadding: 5

            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font.pointSize: root.mini ? 7.85 : 9.8
            color: COMMON.fg3
        }

        Rectangle {
            visible: valueInput.activeFocus
            width: valueInput.implicitWidth
            anchors.right: valueInput.right
            anchors.top: valueInput.top
            anchors.bottom: valueInput.bottom
            anchors.margins: root.mini ? 0 : 1
            border.color: COMMON.bg4
            color: COMMON.bg1
        }

        STextInput {
            anchors.right: spinnerControls.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 2
            width: contentWidth + 10

            id: valueInput
            color: COMMON.fg1
            font.pointSize: root.mini ? 7.7 : 9.6
            activeFocusOnPress: false
            leftPadding: 5
            rightPadding: 5
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            text: root.value.toFixed(root.precValue)
            validator: DoubleValidator {
                bottom: root.minValue
                top: bounded ? root.maxValue : 2147483647.0
            }
            onEditingFinished: {
                root.value = parseFloat(text)
            }
            onActiveFocusChanged: {
                if(!activeFocus) {
                    valueInput.text =  Qt.binding(function() { return root.value.toFixed(root.precValue) })
                }
            }
            
            Keys.onPressed: {
                switch(event.key) {
                    case Qt.Key_Escape:
                        if(root.defaultValue != null) {
                            root.value = root.defaultValue
                            text = root.defaultValue.toFixed(root.precValue)
                        }
                    default:
                        event.accepted = false
                        break;
                }
            }

            MouseArea {
                anchors.fill: parent
                visible: !valueInput.activeFocus
                propagateComposedEvents: true
                onDoubleClicked: {
                    valueInput.forceActiveFocus()
                    valueInput.selectAll()
                }
            }
        }

        Item {
            id: spinnerControls
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 10
            
            Rectangle {
                anchors.top: parent.top
                anchors.right: parent.right
                height: parent.height/2
                width: 10
                color: COMMON.bg4

                Canvas {
                    anchors.fill: parent

                    onPaint: {
                        var context = getContext("2d");
                        var o = root.mini ? 2.75 : 2;
                        var f = root.mini ? 0.75 : -1;
                        context.reset();
                        context.moveTo(o, f+height-o);
                        context.lineTo(width-o, f+height-o);
                        context.lineTo(width / 2,f+height-(width-o));
                        context.lineTo(o,f+height-o);
                        context.closePath();
                        context.fillStyle = COMMON.bg6;
                        context.fill();
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    preventStealing: true
                    onPressed: {
                        root.value = Math.min(root.value + root.incValue, root.maxValue)
                    }
                }

            }

            Rectangle {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                height: parent.height/2
                width: 10
                color: COMMON.bg4

                Canvas {
                    anchors.fill: parent

                    onPaint: {
                        var context = getContext("2d");
                        var o = root.mini ? 2.75 : 2;
                        var f = root.mini ? -0.75 : 1;
                        context.reset();
                        context.moveTo(o, f+o);
                        context.lineTo(width-o, f+o);
                        context.lineTo(width / 2, f+width-o);
                        context.lineTo(o,f+o);
                        context.closePath();
                        context.fillStyle = COMMON.bg6;
                        context.fill();
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    preventStealing: true

                    onPressed: {
                        root.value = Math.max(root.value - root.incValue, root.minValue)
                    }
                }
            }
        }
    }

    Rectangle {
        visible: root.activeFocus
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0

        color: "transparent"
        border.color: COMMON.bg7
    }

    Keys.onPressed: {
        event.accepted = true
        switch(event.key) {
        case Qt.Key_Delete:
            root.deactivate()
            break;
        default:
            event.accepted = false
            break;
        }
    }
}