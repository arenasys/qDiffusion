import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: root
    property var label: "Label"
    property var value: ""
    property var defaultValue: null
    property var mini: height == 20
    property var validator: RegExpValidator { regExp: /.*/ }
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
    }

    onValueChanged: {
        if(root.bindMap != null && root.bindKey != null) {
            root.bindMap.set(root.bindKey, root.value)
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        anchors.bottomMargin: 0

        color: COMMON.bg3
        border.color: COMMON.bg4

        SText {
            id: labelText
            text: root.label
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            leftPadding: 5
            verticalAlignment: Text.AlignVCenter
            font.pointSize: root.mini ? 7.85 : 9.8
            color: COMMON.fg1
        }

        STextInput {
            id: valueText
            text: root.value
            anchors.left: labelText.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            rightPadding: 5
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            font.pointSize: root.mini ? 7.85 : 9.8
            color: COMMON.fg1
            monospace: true
            validator: root.validator
            
            onEditingFinished: {
                root.value = text
            }

            onActiveFocusChanged: {
                if(!activeFocus) {
                    if(acceptableInput) {
                        root.value = text
                    } else {
                        text = root.value
                    }

                    valueText.text = Qt.binding(function() { return root.value; })
                }
            }

            Keys.onPressed: {
                switch(event.key) {
                    case Qt.Key_Escape:
                        if(root.defaultValue != null) {
                            root.value = root.defaultValue
                            text = defaultValue
                        }
                    default:
                        event.accepted = false
                        break;
                }
            }

        }
    }
}