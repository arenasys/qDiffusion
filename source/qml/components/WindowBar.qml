import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"

SMenuBar {
    id: root
    SMenu {
        id: menu
        title: "File"
        SMenu {
            title: "Import"
            Repeater {
                property var tmp: ["Checkpoints", "Components", "LoRAs", "Hypernets", "Embeddings", "Upscalers"]
                model: tmp
                SMenuItem {
                    text: modelData
                }
            }
        }
        SMenu {
            title: "Visit"
            Repeater {
                property var tmp: ["Checkpoints", "Components", "LoRAs", "Hypernets", "Embeddings", "Upscalers"]
                model: tmp
                SMenuItem {
                    text: modelData
                }
            }
        }
        SMenuSeparator {}
        SMenuItem {
            text: "Update"
            onPressed: {
                GUI.currentTab = "Settings"
                SETTINGS.currentTab = "Program"
                SETTINGS.update()
            }
        }
        SMenuItem {
            text: "Reload"
            shortcut: "Ctrl+R"
            onPressed: {
                SETTINGS.restart()
            }

        }
        SMenuSeparator {}
        SMenuItem {
            text: "Quit"
            shortcut: "Ctrl+Q"
            onPressed: {
                GUI.quit()
            }
        }
    }
    SMenu {
        title: "Edit"
        SMenuItem {
            text: "Action"
        }
    }
    SMenu {
        title: "View"
        SMenuItem {
            text: "Action"
        }
    }
    SMenu {
        title: "Help"
        SMenuItem {
            text: "About"
            onPressed: {
                GUI.openLink("https://github.com/arenasys/qDiffusion")
            }
        }
    }
}