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
    property var override: ""
    property var defaultValue: null
    property var mini: height == 20
    property var validator: RegExpValidator { regExp: /.*/ }
    property var disabled: false
    property var overlay: disabled
    property alias active: valueText.activeFocus

    property variant bindMap: null
    property var bindKey: null

    Connections {
        target: bindMap
        function onUpdated(key) {
            if(key == bindKey) {
                var v = control.bindMap.get(control.bindKey)
                if(v != control.value) {
                    control.value = v
                }
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

        color: COMMON.bg2_5
        border.color: COMMON.bg4

        SText {
            id: labelText
            text: control.label
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            verticalAlignment: Text.AlignVCenter
            pointSize: control.mini ? 7.85 : COMMON.pointLabel
            color: COMMON.fg1_5
            monospace: false
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
                pointSize: control.mini ? 7.85 : COMMON.pointValue
                color: COMMON.fg0
                monospace: true
                validator: control.validator
                readOnly: control.disabled
                
                onEditingFinished: {
                    if(text == "") {
                        control.value = defaultValue
                        text = defaultValue
                    } else {
                        control.value = text
                    }
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
                        if(valueText.text == control.defaultValue && control.defaultValue == "-1") {
                            valueText.text = ""
                        }
                        valueText.selectAll()
                    }
                }

                Keys.onPressed: {
                    switch(event.key) {
                        case Qt.Key_Escape:
                            if(control.defaultValue != null) {
                                if(control.defaultValue == "-1") {
                                    control.value = ""
                                    text = ""
                                } else {
                                    control.value = control.defaultValue
                                    text = defaultValue
                                }
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
            pointSize: control.mini ? 7.85 : 9.8
            color: COMMON.fg2
            monospace: true
            text: control.placeholder
            visible: control.value == "" && !valueText.activeFocus
        }

        Rectangle {
            visible: overrideText.visible
            anchors.fill: overrideText
            color: COMMON.bg2_5
            anchors.margins: 2
        }

        SText {
            id: overrideText
            anchors.left: labelText.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            color: COMMON.fg2
            pointSize: 9.8
            monospace: true
            rightPadding: 7

            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            
            text: control.override
            visible: control.override != ""
        }

        Rectangle {
            anchors.fill: parent
            visible: control.overlay
            color: "#90101010"
        }

        Rectangle {
            anchors.fill: parent
            visible: control.disabled
            color: "#c0101010"
            
            MouseArea {
                anchors.fill: parent
            }
        }
    }
}