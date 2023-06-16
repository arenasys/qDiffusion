import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

MenuSeparator {
    height: visible ? 13 : 0
    leftPadding: 1
    rightPadding: 1
    contentItem: Rectangle {
        implicitHeight: 1
        color: COMMON.bg4
    }
}