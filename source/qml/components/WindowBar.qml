import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1

import gui 1.0

import "../style"

SMenuBar {
    id: root

    function tr(str, file = "WindowBar.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    SMenu {
        id: menu
        title: root.tr("File")
        clipShadow: true
        SMenu {
            title: root.tr("Import")
            clipShadow: true
            Repeater {
                property var tmp: ["Checkpoint", "Component", "LoRA", "Embedding", "Upscaler"]
                model: tmp
                SMenuItem {
                    text: root.tr(modelData)

                    onPressed: {
                        importFileDialog.mode = EXPLORER.getMode(modelData+"s")
                        importFileDialog.open()
                    }
                }
            }

            FileDialog {
                id: importFileDialog
                nameFilters: [root.tr("Model files") + " (*.pt *.pth *.ckpt *.bin *.safetensors *.st)"]
                property var mode: ""

                onAccepted: {
                    if(GUI.isRemote) {
                        GUI.currentTab = "Settings"
                        SETTINGS.currentTab = "Remote"
                        var modeIndex = ["checkpoint","component","lora","embedding","upscaler","controlnet"].indexOf(mode)
                        modeIndex = Math.max(modeIndex - 1, 0)
                        SETTINGS.setUpload(file, modeIndex)
                    } else {
                        GUI.currentTab = "Models"
                        EXPLORER.setCurrent(mode, "")
                        GUI.importModel(mode, file)
                    }
                }
            }
        }
        SMenuSeparator {}
        SMenuItem {
            text: root.tr("Update")
            onPressed: {
                GUI.currentTab = "Settings"
                SETTINGS.currentTab = "Program"
                SETTINGS.update()
            }
        }
        SMenuItem {
            text: root.tr("Reload")
            shortcut: "Ctrl+R"
            global: true
            onPressed: {
                SETTINGS.restart()
            }

        }
        SMenuSeparator {}
        SMenuItem {
            text: root.tr("Quit")
            shortcut: "Ctrl+Q"
            global: true
            onPressed: {
                GUI.quit()
            }
        }
    }
    SMenu {
        title: root.tr("Edit")
        clipShadow: true
        SMenuItem {
            text: root.tr("Refresh models")

            onPressed: {
                GUI.refreshModels()
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Generate"
            text: root.tr("Build model")
            onPressed: {
                BASIC.doBuildModel()
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Generate" || GUI.currentTab == "Merge"
            text: root.tr("XY Grid")
            onPressed: {
                if(GUI.currentTab == "Generate") {
                    BASIC.grid.openGrid()
                } else {
                    MERGER.grid.openGrid()
                }
            }
        }
    }
    SMenu {
        title: root.tr("View")
        clipShadow: true
        SMenuItem {
            visible: GUI.currentTab == "Generate"
            text: root.tr("Swap side")
            checkable: true
            checked: GUI.config != null ? GUI.config.get("swap") : false
            onCheckedChanged: {
                GUI.config.set("swap", checked)
                checked = Qt.binding(function () { return GUI.config != null ? GUI.config.get("swap") : false; })
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Generate"
            text: root.tr("Autocomplete")
            checkable: true
            checked: GUI.config != null ? GUI.config.get("autocomplete") > 0 : false
            onCheckedChanged: {
                if(GUI.config.get("autocomplete") > 0 == checked) {
                    return
                }

                if(checked) {
                    GUI.config.set("autocomplete", 1)
                } else {
                    GUI.config.set("autocomplete", 0)
                }
                checked = Qt.binding(function () { return GUI.config != null ? GUI.config.get("autocomplete") > 0 : false; })
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "Models"
            text: root.tr("Thumbails")
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
            text: root.tr("Zoom in")
            shortcut: "Ctrl+="
            onPressed: {
                EXPLORER.adjustCellSize(100)
            }
        }
        SMenuItem {
            visible: GUI.currentTab == "Models"
            text: root.tr("Zoom out")
            shortcut: "Ctrl+-"
            onPressed: {
                EXPLORER.adjustCellSize(-100)
            }
        }

        SMenuItem {
            visible: GUI.currentTab == "History"
            text: root.tr("Zoom in")
            shortcut: "Ctrl+="
            onPressed: {
                GALLERY.adjustCellSize(50)
            }
        }
        SMenuItem {
            visible: GUI.currentTab == "History"
            text: root.tr("Zoom out")
            shortcut: "Ctrl+-"
            onPressed: {
                GALLERY.adjustCellSize(-50)
            }
        }
    }
    SMenu {
        title: root.tr("Help")
        clipShadow: true

        SMenuItem {
            text: root.tr("Open Guide")
            onPressed: {
                GUI.openLink("https://github.com/arenasys/qDiffusion/wiki/Guide")
            }
        }
        SMenuItem {
            text: root.tr("Report Issue")
            onPressed: {
                GUI.openLink("https://github.com/arenasys/qDiffusion/issues/new?assignees=&labels=&projects=&template=bug_report.md&title=")
            }
        }
        SMenuSeparator {}
        SMenu {
            title: root.tr("Get Model")
            width: 100
            SMenuItem {
                text: root.tr("SD-v1")
                onPressed: {
                    SETTINGS.download("SD", "https://huggingface.co/datasets/arenasys/qDiffusion/blob/main/SD-v1.safetensors")
                }
            }
            SMenuItem {
                text: root.tr("SD-v2")
                onPressed: {
                    SETTINGS.download("SD", "https://huggingface.co/datasets/arenasys/qDiffusion/blob/main/SD-v2.safetensors")
                }
            }
            SMenuItem {
                text: root.tr("SDXL")
                onPressed: {
                    SETTINGS.download("SD", "https://huggingface.co/datasets/arenasys/qDiffusion/blob/main/SDXL.safetensors")
                }
            }
        }
        SMenuSeparator {}
        SMenuItem {
            text: root.tr("About")
            onPressed: {
                GUI.openLink("https://github.com/arenasys/qDiffusion")
            }
        }
    }
}