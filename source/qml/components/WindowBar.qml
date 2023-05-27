import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1

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
                property var tmp: ["Checkpoint", "Component", "LoRA", "Hypernet", "Embedding", "Upscaler"]
                model: tmp
                SMenuItem {
                    text: modelData

                    onPressed: {
                        importFileDialog.mode = EXPLORER.getMode(modelData+"s")
                        importFileDialog.open()
                    }
                }
            }

            FileDialog {
                id: importFileDialog
                nameFilters: ["Model file (*.pt *.pth *.ckpt *.bin *.safetensors *.st)"]
                property var mode: ""

                onAccepted: {
                    
                    if(GUI.remoteStatus != 0) {
                        GUI.currentTab = "Settings"
                        SETTINGS.currentTab = "Remote"
                        SETTINGS.currentUpload = file
                        SETTINGS.setUploadMode(mode)
                    } else {
                        GUI.currentTab = "Models"
                        EXPLORER.currentTab = mode
                        GUI.importModel(mode, file)
                    }
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