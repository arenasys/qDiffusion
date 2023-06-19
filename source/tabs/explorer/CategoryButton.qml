import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

SColumnButton {
    id: root

    function tr(str, file = "CategoryButton.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    property var mode
    label: root.tr(EXPLORER.getLabel(mode), "Category")
    active: EXPLORER.currentTab == mode

    signal move(string model, string folder, string subfolder)
    
    onPressed: {
        EXPLORER.setCurrent(mode, "")
    }

    AdvancedDropArea {
        id: basicDrop
        anchors.fill: parent
        onContainsDragChanged: {
            if(containsDrag) {
                dragTimer.start()
            } else {
                dragTimer.stop()
            }
        }
        Timer {
            id: dragTimer
            interval: 200
            onTriggered: {
                EXPLORER.setCurrent(mode, "")
            }
        }
        onDropped: {
            var model = EXPLORER.onDrop(mimeData)
            if(model != "") {
                root.move(model, mode, "")
            }
        }
    }
}