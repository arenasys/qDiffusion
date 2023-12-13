import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root

    function tr(str, file = "HostSettings.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    Column {
        anchors.centerIn: parent
        height: parent.height-100
        width: parent.width/2

        OChoice {
            id: hostEnabled
            property var hosting: currentIndex == 1
            x: -2
            width: parent.width+2
            height: 30
            label: root.tr("Hosting")
            entries: [root.tr("Disabled", "General"), root.tr("Enabled", "General")]

            currentIndex: GUI.config.get("host_enabled") ? 1 : 0 
            onCurrentIndexChanged: {
                GUI.config.set("host_enabled", currentIndex != 0)
            }
        }

        SButton {
            x: -2
            width: parent.width+2
            height: 30
            label: root.tr("Reload")
            onPressed: {
                GUI.config.set("endpoint", "")
                SETTINGS.restart()
            }
        }

        Item {
            width: parent.width
            height: 5
        }

        STextSelectable {
            text: GUI.hostEndpoint != "" ? root.tr("Endpoint: %1").arg(GUI.hostEndpoint) : root.tr("Inactive")
            width: parent.width
            height: 25
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            pointSize: 9.8
            color: GUI.hostEndpoint != "" ? COMMON.fg2 : COMMON.accent(0)
        }

        STextSelectable {
            text: root.tr("Password: %1").arg(GUI.hostPassword)
            width: parent.width
            height: visible ? 25 : 0
            visible: GUI.hostPassword != ""
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            pointSize: 9.8
            color: COMMON.fg2
        }

        SText {
            text: "Web: https://arenasys.github.io/?..."
            width: parent.width
            height: visible ? 25 : 0
            visible: GUI.hostWeb != ""
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            pointSize: 9.8
            font.underline: linkMouse.containsMouse
            color: COMMON.fg2
            MouseArea {
                id: linkMouse
                hoverEnabled: true
                visible: parent.visible
                anchors.fill: parent
                onPressed: {
                    Qt.openUrlExternally(GUI.hostWeb)
                }
            }
        }

        Item {
            visible: GUI.hostPassword == ""
            width: parent.width
            height: visible ? 25 : 0
            LoadingSpinner {
                visible: GUI.remoteInfoMode == "Host"
                size: 20
                running: visible
                anchors.fill: parent
            }
        }
        
        Item {
            width: parent.width
            height: 5
        }

        Item {
            width: parent.width
            height: 30
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 30
                label: root.tr("Address")
                disabled: !hostEnabled.hosting

                value: GUI.config.get("host_address")

                onValueChanged: {
                    GUI.config.set("host_address", value)
                }
            }
        }

        Item {
            width: parent.width
            height: 30
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 30
                label: root.tr("Port")
                disabled: !hostEnabled.hosting

                value: GUI.config.get("host_port")

                onValueChanged: {
                    GUI.config.set("host_port", value)
                }
            }
        }

        Item {
            width: parent.width
            height: 30
            OTextInput {
                anchors.leftMargin: -2
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 30
                label: root.tr("Password")
                value: ""
                placeholder: root.tr("Random")
                disabled: !hostEnabled.hosting

                onValueChanged: {
                    GUI.hostPassword = value
                }
            }
        }

        Row {
            x: -2
            width: parent.width+2
            height: 30
            OChoice {
                width: parent.width / 3
                height: 30
                rightPadding: false
                label: root.tr("Tunnel")
                entries: [root.tr("Disabled", "General"), root.tr("Enabled", "General")]
                disabled: !hostEnabled.hosting

                currentIndex: GUI.config.get("host_tunnel") ? 1 : 0 
                onCurrentIndexChanged: {
                    GUI.config.set("host_tunnel", currentIndex != 0)
                }
            }
            OChoice {
                width: parent.width / 3
                height: 30
                rightPadding: false
                label: root.tr("Read-only")
                entries: [root.tr("Disabled", "General"), root.tr("Enabled", "General")]
                disabled: !hostEnabled.hosting

                currentIndex: GUI.config.get("host_read_only") ? 1 : 0 
                onCurrentIndexChanged: {
                    GUI.config.set("host_read_only", currentIndex != 0)
                }
            }
            OChoice {
                width: parent.width / 3
                height: 30
                label: root.tr("Monitor")
                entries: [root.tr("Disabled", "General"), root.tr("Enabled", "General")]
                disabled: !hostEnabled.hosting

                currentIndex: GUI.config.get("host_monitor") ? 1 : 0 
                onCurrentIndexChanged: {
                    GUI.config.set("host_monitor", currentIndex != 0)
                }
            }
        }
    }
}