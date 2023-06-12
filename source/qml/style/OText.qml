import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

SText {
    id: control

    property var defaultText: null

    property variant bindMap: null
    property var bindKey: null

    function display(text) {
        return text
    }

    Connections {
        target: bindMap
        function onUpdated() {
            var v = control.bindMap.get(control.bindKey)
            if(v != control.text) {
                control.text = control.display(v)
            }
        }
    }

    Component.onCompleted: {
        if(control.bindMap != null && control.bindKey != null) {
            control.text = control.display(control.bindMap.get(control.bindKey))
        }
        if(control.defaultText == null) {
            control.defaultText = control.text;
        }
    }

    onTextChanged: {
        if(control.bindMap != null && control.bindKey != null) {
            control.bindMap.set(control.bindKey, control.text)
        }
    }
}