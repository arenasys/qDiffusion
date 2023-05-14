import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.15

import gui 1.0

Menu {
    id: root
    readonly property real menuItemSize: 20
    topPadding: 2
    bottomPadding: 2

    delegate: SContextMenuItem {
        menuItemSize: root.menuItemSize
    }

    background: RectangularGlow {
        implicitWidth: 150
        implicitHeight: menuItemSize
        glowRadius: 5
        //spread: 0.2
        color: "black"
        cornerRadius: 10

        Rectangle {
            anchors.fill: parent
            color: COMMON.bg3
            border.width: 1
            border.color: COMMON.bg4
        }
    }
}
