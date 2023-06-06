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
        clipShadow: true
        SMenu {
            title: "Import"
            clipShadow: true
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
            global: true
            onPressed: {
                SETTINGS.restart()
            }

        }
        SMenuSeparator {}
        SMenuItem {
            text: "Quit"
            shortcut: "Ctrl+Q"
            global: true
            onPressed: {
                GUI.quit()
            }
        }
    }
    SMenu {
        title: "Edit"
        clipShadow: true
        SMenuItem {
            text: "Refresh models"   
        }

        SMenuItem {
            visible: GUI.currentTab == "Basic"
            height: visible ? 20 : 0
            text: "Build model"
            onPressed: {
                BASIC.doBuildModel()
            }
        }
    }
    SMenu {
        title: "View"
        clipShadow: true
        SMenuItem {
            visible: GUI.currentTab == "Basic"
            height: visible ? 20 : 0
            text: "Swap side"
            checkable: true
            checked: GUI.config != null ? GUI.config.get("swap") : false
            onCheckedChanged: {
                GUI.config.set("swap", checked)
                checked = Qt.binding(function () { return GUI.config != null ? GUI.config.get("swap") : false; })
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Models"
            height: visible ? 20 : 0
            text: "Thumbails"
            shortcut: "Shift"
            checkable: true
            checked: !EXPLORER.showInfo
            onCheckedChanged: {
                if(checked != !EXPLORER.showInfo) {
                    EXPLORER.showInfo = !checked
                    checked = Qt.binding(function () { return !EXPLORER.showInfo; })
                }
            }
        }
        SMenuItem {
            visible: GUI.currentTab == "Models"
            height: visible ? 20 : 0
            text: "Zoom in"
            shortcut: "Ctrl+="
            onPressed: {
                EXPLORER.adjustCellSize(100)
            }
        }
        SMenuItem {
            visible: GUI.currentTab == "Models"
            height: visible ? 20 : 0
            text: "Zoom out"
            shortcut: "Ctrl+-"
            onPressed: {
                EXPLORER.adjustCellSize(-100)
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Gallery"
            height: visible ? 20 : 0
            text: "Zoom in"
            shortcut: "Ctrl+="
            onPressed: {
                GALLERY.adjustCellSize(50)
            }
        }
        SMenuItem {
            visible: GUI.currentTab == "Gallery"
            height: visible ? 20 : 0
            text: "Zoom out"
            shortcut: "Ctrl+-"
            onPressed: {
                GALLERY.adjustCellSize(-50)
            }
        }
    }
    SMenu {
        title: "Help"
        clipShadow: true
        SMenuItem {
            text: "About"
            onPressed: {
                GUI.openLink("https://github.com/arenasys/qDiffusion")
            }
        }
    }
}