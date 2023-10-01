
import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

Item {
    id: root

    property var currentTab: GUI.currentTab

    function tr(str, file = "TabBar.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }
    
    height: 30

    STabBar {
        id: leftBar
        anchors.left: root.left
        anchors.right: rightBar.right
        anchors.top: root.top

        contentHeight: 30

        Repeater {
            model: GUI.visibleTabs
            STabButton {
                text: root.tr(modelData, "Tabs")
                selected: GUI.currentTab == modelData
                working: GUI.workingTabs.includes(modelData)
                onPressed: {
                    GUI.currentTab = modelData
                }
                onDragEnter: {
                    GUI.currentTab = modelData
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
            text: root.tr(rightBar.settingsName)
            selected: GUI.currentTab == rightBar.settingsName
            onPressed: {
                GUI.currentTab = rightBar.settingsName
            }
        }

        STabButton {
            text: "▼"
            width: 35
            selected: dropdownContextMenu.activeFocus
            pointSize: 9

            onPressed: {
                dropdownContextMenu.popup(0,height)
            }
        }

        SContextMenu {
            id: dropdownContextMenu

            Repeater {
                property var tmp: GUI.tabNames.slice(0,-1)
                model: tmp
                SContextMenuItem {
                    property var name: modelData
                    text: root.tr(modelData, "Tabs")
                    checkable: true
                    checked: GUI.visibleTabs.includes(modelData)

                    onCheckedChanged: {
                        GUI.setTabVisible(modelData, checked)
                    }
                }
            }
        }
    }
}
