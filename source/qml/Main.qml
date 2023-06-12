import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

FocusReleaser {
    property var window
    anchors.fill: parent  
    
    Component.onCompleted: {
        window.title = Qt.binding(function() { return root.tr(GUI.title); })
    }

    Rectangle {
        id: root
        anchors.fill: parent
        color: COMMON.bg0
        
        function tr(str, file = "Main.qml") {
            return TRANSLATOR.instance.translate(str, file)
        }
    }

    WindowBar {
        id: windowBar
        anchors.left: root.left
        anchors.right: root.right
    }

    TabBar {
        id: tabBar
        anchors.left: root.left
        anchors.right: root.right
        anchors.top: windowBar.bottom
    }

    Rectangle {
        id: barDivider
        anchors.left: root.left
        anchors.right: root.right
        anchors.top: tabBar.bottom

        height: 5
        color: COMMON.bg4
    }

    ErrorDialog {
        id: errorDialog
    }

    StackLayout {
        id: stackLayout
        anchors.left: root.left
        anchors.right: root.right
        anchors.top: barDivider.bottom
        anchors.bottom: statusBar.top

        currentIndex: GUI.tabNames.indexOf(GUI.currentTab)

        function releaseFocus() {
            keyboardFocus.forceActiveFocus()
        }

        function addTab() {
            for(var i = 0; i < GUI.tabSources.length; i++) {
                var component = Qt.createComponent(GUI.tabSources[i])
                if(component.status != Component.Ready) {
                    console.log("ERROR", component.errorString())
                } else {
                    component.createObject(stackLayout)
                }
            }
        }

        Component.onCompleted: {
            addTab()
        }

        onCurrentIndexChanged: {
            releaseFocus()
        }
    }

    StatusBar {
        id: statusBar
        anchors.left: root.left
        anchors.right: root.right
        anchors.bottom: root.bottom
        height: stackLayout.currentIndex == 0 ? 0 : 20
    }

    onReleaseFocus: {
        keyboardFocus.forceActiveFocus()
    }

    Shortcut {
        sequences: COMMON.keys_basic
        onActivated: GUI.currentTab = "Basic"
    }

    Shortcut {
        sequences: COMMON.keys_models
        onActivated: GUI.currentTab = "Models"
    }

    Shortcut {
        sequences: COMMON.keys_gallery
        onActivated: GUI.currentTab = "Gallery"
    }

    Shortcut {
        sequences: COMMON.keys_settings
        onActivated: GUI.currentTab = "Settings"
    }

    Item {
        id: keyboardFocus
        Keys.onPressed: {
            event.accepted = true
            if(event.modifiers & Qt.ControlModifier) {
                switch(event.key) {
                default:
                    event.accepted = false
                    break;
                }
            } else {
                switch(event.key) {
                default:
                    event.accepted = false
                    break;
                }
            }
        }
        Keys.forwardTo: [stackLayout.children[stackLayout.currentIndex]]
    }
}