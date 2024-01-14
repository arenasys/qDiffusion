import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

FocusReleaser {
    property var window
    property var spinner
    anchors.fill: parent
    layer.enabled: true
    opacity: 0.0

    NumberAnimation on opacity {
        id: opacityAnimator
        from: 0
        to: 1
        duration: 250
        onFinished: {
            layer.enabled = false
            spinner.visible = false
        }
    }
    
    Component.onCompleted: {
        window.title = Qt.binding(function() { return TRANSLATOR.instance.translate(GUI.title, "Title"); })
        opacityAnimator.start()
    }

    Timer {
        id: raiseTimer
        interval: 50
        onTriggered: {
            window.flags = Qt.Window
            window.requestActivate()
        }
    }

    Connections {
        target: GUI
        function onRaiseToTop() {
            window.flags = Qt.Window | Qt.WindowStaysOnTopHint
            raiseTimer.start()
        }
    }


    Rectangle {
        id: root
        anchors.fill: parent
        color: COMMON.bg0
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
            var errorTab = Qt.createComponent("qrc:/Error.qml")
            for(var i = 0; i < GUI.tabSources.length; i++) {
                var component = Qt.createComponent(GUI.tabSources[i])
                if(component.status != Component.Ready) {
                    var errorString = component.errorString()
                    console.log("ERROR", errorString)
                    errorTab.createObject(stackLayout, {error: errorString})
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
        onActivated: GUI.currentTab = "Generate"
    }

    Shortcut {
        sequences: COMMON.keys_models
        onActivated: GUI.currentTab = "Models"
    }

    Shortcut {
        sequences: COMMON.keys_gallery
        onActivated: GUI.currentTab = "History"
    }

    Shortcut {
        sequences: COMMON.keys_merge
        onActivated: GUI.currentTab = "Merge"
    }

    /*Shortcut {
        sequences: COMMON.keys_train
        onActivated: GUI.currentTab = "Train"
    }*/

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