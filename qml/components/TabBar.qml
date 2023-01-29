
import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    id: root

    property var currentTab: GUI.tabNames[0]
    property var shown: GUI.tabNames.slice(0,-1)

    function getShown() {
        var _shown = []
        var i = 0
        while (true) {
            var action = dropdownContextMenu.itemAt(i++)
            if(action == null) {
                break
            } else if(action.checked) {
                _shown.push(action.text)
            }
        }
        shown = _shown
        
        if(shown.indexOf(currentTab) == -1) {
            currentTab = "Settings"
        }
    }
    
    height: 30

    STabBar {
        id: leftBar
        anchors.left: root.left
        anchors.right: rightBar.right
        anchors.top: root.top

        contentHeight: 30

        Repeater {
            model: shown
            STabButton {
                text: qsTr(modelData)
                selected: root.currentTab == modelData
                onPressed: {
                    root.currentTab = modelData
                }
            }
        }
    }

    STabBar {
        id: rightBar
        anchors.right: root.right
        anchors.top: root.top
        contentHeight: 30

        property var settingsName: GUI.tabNames.slice(-1)[0] 

        STabButton {
            text: qsTr(rightBar.settingsName)
            selected: root.currentTab == rightBar.settingsName
            onPressed: {
                root.currentTab = rightBar.settingsName
            }
        }

        STabButton {
            text: "▼"
            width: 35
            selected: dropdownContextMenu.activeFocus

            onPressed: {
                dropdownContextMenu.popup(0,height)
            }
        }

        SContextMenu {
            id: dropdownContextMenu

            Repeater {
                model: GUI.tabNames.slice(0,-1)
                SContextMenuItem {
                    text: modelData
                    checkable: true
                    checked: true

                    onCheckedChanged: {
                        root.getShown()
                    }
                }
            }
        }
    }
}
