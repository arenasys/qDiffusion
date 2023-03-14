import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"

Rectangle {
    color: "#f00"

    Button {
        text: "Generate"
        onClicked: GUI.generate()
    }
}