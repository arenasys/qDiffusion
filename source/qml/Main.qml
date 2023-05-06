import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

FocusReleaser {
    anchors.fill: parent

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

        onCurrentTabChanged: {
            if(currentTab == "Gallery") {
                GALLERY.awaken()
            }
        }
    }

    Rectangle {
        id: barDivider
        anchors.left: root.left
        anchors.right: root.right
        anchors.top: tabBar.bottom

        height: 5
        color: COMMON.bg4
    }

    SDialog {
        id: dialog
        title: "Error"
        standardButtons: Dialog.Ok
        modal: true
        dim: true

        width: errorText.contentWidth + 50
        height: errorText.contentHeight + 80

        SText {
            id: errorText
            anchors.centerIn: parent
            padding: 5
            text: "Error while " + GUI.errorStatus + ".\n" + GUI.errorText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            width: Math.min(errorText.implicitWidth, 500)
            wrapMode: Text.Wrap
        }

        onClosed: {
            GUI.clearError()
        }

        Connections {
            target: GUI
            function onErrorTextChanged() {
                dialog.open()
            }
        }
    }

    StackLayout {
        id: stackLayout
        anchors.left: root.left
        anchors.right: root.right
        anchors.top: barDivider.bottom
        anchors.bottom: statusBar.top

        currentIndex: GUI.tabNames.indexOf(tabBar.currentTab)


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
        sequence: "Ctrl+1"
        onActivated: tabBar.setIndex(0)
    }

    Shortcut {
        sequence: "Ctrl+2"
        onActivated: tabBar.setIndex(1)
    }

    Shortcut {
        sequence: "Ctrl+3"
        onActivated: tabBar.setIndex(2)
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