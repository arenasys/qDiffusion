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
    property var mode
    label: EXPLORER.getLabel(mode)
    active: EXPLORER.currentTab == mode

    signal move(string model, string folder, string subfolder)
    
    onPressed: {
        EXPLORER.currentTab = mode
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
                EXPLORER.currentTab = mode
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