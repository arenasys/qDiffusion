import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "style"
import "components"

Item {
    anchors.fill: parent
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

            width: errorText.implicitWidth + 50
            height: errorText.contentHeight + 80

            SText {
                id: errorText
                anchors.fill: parent
                padding: 5
                text: "Error while " + GUI.errorStatus + ".\n" + GUI.errorText
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
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
            anchors.bottom: root.bottom

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

        onReleaseFocus: {
            keyboardFocus.forceActiveFocus()
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
}