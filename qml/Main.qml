import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

ApplicationWindow {
    visible: true
    width: 1100
    height: 600
    title: GUI.title
    id: root
    color: "#000"

    WindowBar {
        anchors.left: parent.left
        anchors.right: parent.right
    }
}