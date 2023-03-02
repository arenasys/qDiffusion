import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Item {
    id: root
    height: 30
    property var mini: height == 20

    property var label: "Label"
    property var value: 50
    property var minValue: 0
    property var maxValue: 100
    property var precValue: 0
    property var incValue: 1
    property var labelWidth: 70
    property var valueWidth: mini ? 30 : 40

    function update(pos) {
        var value = pos*(root.maxValue-root.minValue) + root.minValue
        value = parseFloat(value.toFixed(root.precValue))
        root.value = value
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

            function update() {
                root.update(Math.min(width, Math.max(0, mouseX))/width)
            }

            onPressed: {
                mouseArea.update()
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
            width: (mouseArea.width) * (root.value - root.minValue)/(root.maxValue-root.minValue)
        }

        SText {
            id: labelText
            text: root.label
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            rightPadding: 5
            width: root.labelWidth
            verticalAlignment: Text.AlignVCenter
            font.pointSize: root.mini ? 7.85 : 9.8
            color: COMMON.fg1
        }

        Rectangle {
            id: valueArea
            anchors.right: spinnerControls.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 2
            width: root.valueWidth

            clip: true

            color: valueInput.activeFocus ? "#40000000" : "transparent"
            border.color: valueInput.activeFocus ? "#10ffffff" : "transparent"
            border.width: 1.5

            STextInput {
                id: valueInput
                color: COMMON.fg1
                font.pointSize: root.mini ? 7.7 : 9.6
                activeFocusOnPress: false
                anchors.fill: parent
                leftPadding: 5
                rightPadding: 5
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                text: root.value.toFixed(root.precValue)
                validator:  DoubleValidator {
                    bottom: root.minValue
                    top: root.maxValue
                }
                onEditingFinished: {
                    root.value = parseFloat(text)
                }
                onActiveFocusChanged: {
                    if(!activeFocus) {
                        valueInput.text =  Qt.binding(function() { return root.value.toFixed(root.precValue) })
                    }
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
}