import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: root
    property var color: COMMON.bg00
    property var shadowColor: "#f0000000"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        color: root.color
    }

    layer.enabled: true
    layer.effect: InnerShadow {
        color: root.shadowColor
        samples: 16
        radius: 16
        spread: 0
        fast: true
    }
}