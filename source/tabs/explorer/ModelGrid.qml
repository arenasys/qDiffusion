import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    property var mode: ""
    property var folder: ""
    property var label: ""
    property var cellSize: EXPLORER.cellSize
    property var descLength: (cellSize*cellSize)/100
    property var showInfo: false
    property var search: ""

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: {
            root.deselect(-1)
        }
        onWheel: {
            if(wheel.angleDelta.y < 0) {
                scrollBar.increase()
            } else {
                scrollBar.decrease()
            }
        }
    }

    signal deleteModel(string model)
    signal deselect(int index)

    SButton {
        visible: modelsView.count == 0 && (GUI.remoteStatus == 0 || root.mode == "wildcard") && root.mode != "favourite"
        anchors.centerIn: root
        width: 150
        height: 27
        label: "Open " + root.label
        color: COMMON.fg1_5

        onPressed: {
            GUI.openModelFolder(root.mode)
        }
    }

    SText {
        anchors.centerIn: parent
        visible: modelsView.count == 0 && GUI.remoteStatus != 0 && root.mode != "wildcard"
        text: "Remote has no " + root.label
        color: COMMON.fg2
        font.pointSize: 9.8
    }

    GridView {
        id: modelsView
        property int padding: 10
        property bool showScroll: modelsView.contentHeight > modelsView.height
        cellWidth: Math.max((modelsView.width - 15)/Math.max(Math.ceil((modelsView.width - 5)/root.cellSize), 1), 50)
        cellHeight: Math.floor(cellWidth*1.33)
        anchors.fill: parent
        footer: Item {
            width: parent.width
            height: 10
        }
        model: Sql {
            id: modelsSql
            query: "SELECT name, type, desc, file, width, height FROM models WHERE category = '" + root.mode + "' AND folder = '" + root.folder + "' AND name LIKE '%" + root.search +"%' ORDER BY idx ASC;"
            property bool reset: false
            debug: root.mode == 'favourite'
            function refresh() {
                modelsView.positionViewAtBeginning()
            }
            onQueryChanged: {
                modelsSql.refresh()
                reset = true
            }
            onResultsChanged: {
                if(reset) {
                    modelsSql.refresh()
                    reset = false
                }
            }
        }

        interactive: false
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
            stepSize: 0.25/Math.ceil(modelsView.count / Math.round(modelsView.width/modelsView.cellWidth))
            policy: modelsView.showScroll ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        }

        delegate: ModelCard {
            grid: root
            onDeleteModel: {
                root.deleteModel(model)
            }
        }
    }
}