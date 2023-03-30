import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: control
    property var label: "Label"
    property var tooltip: ""
    property var value: ""
    property var placeholder: ""
    property var defaultValue: null
    property var mini: height == 20
    property var validator: RegExpValidator { regExp: /.*/ }
    property var disabled: false
    property var overlay: disabled

    property variant bindMap: null
    property var bindKey: null

    Connections {
        target: bindMap
        function onUpdated() {
            var v = control.bindMap.get(control.bindKey)
            if(v != control.value) {
                control.value = v
            }
        }
    }

    Component.onCompleted: {
        if(control.bindMap != null && control.bindKey != null) {
            control.value = control.bindMap.get(control.bindKey)
        }
        if(control.defaultValue == null) {
            control.defaultValue = control.value;
        }
    }

    onValueChanged: {
        if(control.bindMap != null && control.bindKey != null) {
            control.bindMap.set(control.bindKey, control.value)
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0
        clip: true

        color: COMMON.bg3
        border.color: COMMON.bg4

        SText {
            id: labelText
            text: control.label
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            verticalAlignment: Text.AlignVCenter
            font.pointSize: control.mini ? 7.85 : 9.8
            color: COMMON.fg1
        }

        MouseArea {
            id: mouseArea
            anchors.fill: labelText
            hoverEnabled: true
        }

        SToolTip {
            id: infoToolTip
            x: 0
            visible: !disabled && tooltip != "" && mouseArea.containsMouse
            delay: 100
            text: tooltip
        }

        Rectangle {
            visible: valueText.activeFocus
            width: Math.min(container.width+3, valueText.implicitWidth + 5)
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: control.mini ? 1 : 3
            border.color: COMMON.bg4
            color: COMMON.bg1
        }

        Item {
            id: container
            anchors.left: labelText.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.leftMargin: 10
            anchors.rightMargin: control.mini ? 3 : 5
            clip: true

            STextInput {
                id: valueText
                text: control.value
                anchors.fill: parent
                rightPadding: 5
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                font.pointSize: control.mini ? 7.85 : 9.8
                color: COMMON.fg1
                monospace: true
                validator: control.validator
                readOnly: control.disabled
                
                onEditingFinished: {
                    control.value = text
                }

                onActiveFocusChanged: {
                    if(!activeFocus) {
                        if(acceptableInput) {
                            control.value = text
                        } else {
                            text = control.value
                        }

                        valueText.text = Qt.binding(function() { return control.value; })
                    } else {
                        valueText.selectAll()
                    }
                }

                Keys.onPressed: {
                    switch(event.key) {
                        case Qt.Key_Escape:
                            if(control.defaultValue != null) {
                                control.value = control.defaultValue
                                text = defaultValue
                            }
                            break;
                        default:
                            event.accepted = false
                            break;
                    }
                }
            }
        }

        SText {
            id: placeholderText
            anchors.left: labelText.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            rightPadding: 5
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            font.pointSize: control.mini ? 7.85 : 9.8
            color: COMMON.fg2
            monospace: true
            text: control.placeholder
            visible: control.value == "" && !valueText.activeFocus
        }

        Rectangle {
            anchors.fill: parent
            visible: control.overlay
            color: "#a0101010"
        }
    }
}