import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "style"
import "components"

Item {
    id: root
    property var error: ""

    function tr(str, file = "Error.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    STextSelectable {
        id: errorText
        anchors.fill: parent
        padding: 20
        color: COMMON.fg2
        pointSize: 9.8
        text: root.tr("Error: %1").arg(root.error)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.Wrap
        monospace: true
    }
}