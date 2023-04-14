import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.0

import gui 1.0

import "../style"

Item {
    id: root
    anchors.fill: parent

    signal generate()
    signal cancel()
    signal buildModel()

    function sizeDrop(mimedata) {
        
    }

    function seedDrop(mimedata) {
        
    }

    property var forever: false
    property var remaining: 0

    property var binding

    Item {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.bottom: parent.bottom

        width: Math.max(150, parent.width)

        GenerateButton {
            id: genButton
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 2
            height: 40

            Timer {
                id: genButtonTimer
                interval: 100
                onTriggered: {
                    genButton.progress = GUI.statusProgress
                    genButton.working = GUI.statusMode == 2
                }
            }
            Connections {
                target: GUI
                function onStatusProgressChanged() {
                    genButtonTimer.restart()
                }
                function onStatusModeChanged() {
                    genButtonTimer.restart()
                }
            }

            progress: -1
            working: false
            disabled: GUI.statusMode == 0 || GUI.statusMode == 3
            info: GUI.statusInfo
            remaining: root.remaining

            onPressed: {
                if(GUI.statusMode == 1) {
                    root.generate()
                }
                if(GUI.statusMode == 2) {
                    root.cancel()
                }
            }

            onContextMenu: {
                genContextMenu.popup()
            }

            SContextMenu {
                id: genContextMenu
                SContextMenuItem {
                    text: "Generate Forever"
                    checkable: true
                    onCheckedChanged: {
                        root.forever = checked
                    }
                }
                SContextMenuItem {
                    height: visible ? 25 : 0
                    visible: GUI.statusMode == 2
                    text: "Cancel"
                    onPressed: {
                        root.cancel()
                    }
                }
            }
        }
        
        Rectangle {
            id: generateDivider
            anchors.top: genButton.bottom
            anchors.topMargin: 2
            anchors.left: parent.left
            anchors.right: parent.right
            height: 4
            color: COMMON.bg4
        }

        Flickable {
            id: paramScroll
            anchors.top: generateDivider.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            clip: true

            contentHeight: paramColumn.height
            contentWidth: parent.width
            boundsBehavior: Flickable.StopAtBounds

            function position(item) {
                var yy = paramScroll.mapFromItem(item, 0, item.height).y - paramScroll.height
                if(yy > 0) {
                    paramScroll.contentY = yy
                }
            }

            Column {
                id: paramColumn
                width: paramScroll.width
                OColumn {
                    id: optColumn
                    text: "Options"
                    width: parent.width

                    onExpanded: {
                        paramScroll.position(optColumn)
                    }

                    OSlider {
                        id: widthInput
                        label: "Width"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "width"

                        minValue: 64
                        maxValue: 1024
                        precValue: 0
                        incValue: 8
                        snapValue: 64
                        bounded: false

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.sizeDrop(mimeData)
                            }
                        }
                    }
                    OSlider {
                        id: heightInput
                        label: "Height"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "height"

                        minValue: 64
                        maxValue: 1024
                        precValue: 0
                        incValue: 8
                        snapValue: 64
                        bounded: false

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.sizeDrop(mimeData)
                            }
                        }
                    }
                    OSlider {
                        id: stepsInput
                        label: "Steps"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "steps"

                        minValue: 0
                        maxValue: 100
                        precValue: 0
                        incValue: 1
                        snapValue: 5
                        bounded: false
                    }
                    OSlider {
                        id: scaleInput
                        label: "Scale"
                        width: parent.width
                        height: 30
                        
                        bindMap: root.binding.values
                        bindKey: "scale"

                        minValue: 1
                        maxValue: 20
                        precValue: 1
                        incValue: 1
                        snapValue: 0.5
                        bounded: false
                    }
                    OTextInput {
                        id: seedInput
                        label: "Seed"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "seed"

                        validator: IntValidator { 
                            bottom: -1
                            top: 2147483646
                        }

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.seedDrop(mimeData)
                            }
                        }
                    }
                }
                OColumn {
                    id: samplerColumn
                    text: "Sampler"
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.position(samplerColumn)
                    }

                    input: OChoice {
                        id: samplerInput
                        label: ""
                        height: 28
                        width: samplerColumn.width - 100

                        bindMap: root.binding.values
                        bindKeyCurrent: "sampler"
                        bindKeyModel: "samplers"
                    }

                    OSlider {
                        id: etaInput
                        label: "Eta"
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKey: "eta"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }
                }
                OColumn {
                    id: modelColumn
                    text: "Model"
                    width: parent.width
                    isCollapsed: true

                    property var componentMode: unetInput.value != vaeInput.value || unetInput.value != clipInput.value

                    onExpanded: {
                        paramScroll.position(modelColumn)
                    }

                    input: OChoice {
                        id: modelInput
                        label: ""
                        width: modelColumn.width - 100
                        height: 28

                        bindMap: root.binding.values
                        bindKeyCurrent: "model"
                        bindKeyModel: "models"

                        tooltip: value

                        overlay: modelColumn.componentMode
                        popupHeight: root.height + 100

                        onSelected: {
                            root.binding.values.set("VAE", value)
                            root.binding.values.set("UNET", value)
                            root.binding.values.set("CLIP", value)
                        }

                        onContextMenu: {
                            modelsContextMenu.popup()
                        }

                        SContextMenu {
                            id: modelsContextMenu
                            SContextMenuItem {
                                text: "Force Refresh"
                                onPressed: {
                                    GUI.refreshModels()
                                }
                            }
                            SContextMenuItem {
                                text: "Build model"
                                onPressed: {
                                    root.buildModel()
                                    modelsContextMenu.close()
                                }
                            }
                        }
                    }

                    property var models: root.binding.values.get("models")

                    OChoice {
                        id: unetInput
                        label: "UNET"
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKeyCurrent: "UNET"
                        bindKeyModel: "UNETs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return "External"
                            }
                            return ""
                        }

                        onSelected: {
                            root.binding.values.set("model", value)
                        }
                    }
                    OChoice {
                        id: vaeInput
                        label: "VAE"
                        width: parent.width
                        height: 25

                        bindMap: root.binding.values
                        bindKeyCurrent: "VAE"
                        bindKeyModel: "VAEs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return "External"
                            }
                            return ""
                        }
                    }
                    OChoice {
                        id: clipInput
                        label: "CLIP"
                        width: parent.width
                        height: 25

                        bindMap: root.binding.values
                        bindKeyCurrent: "CLIP"
                        bindKeyModel: "CLIPs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return "External"
                            }
                            return ""
                        }
                    }
                }

                OColumn {
                    id: netColumn
                    text: "Networks"
                    width: parent.width
                    padding: false
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.position(netColumn)
                    }

                    Item {
                        width: parent.width
                        height: Math.min(200, 32+(netList.contentHeight == 0 ? 0 : netList.contentHeight+3))

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 2
                            color: "transparent"
                            border.color: COMMON.bg4
                            border.width: 1

                            Item {
                                anchors.top: parent.top
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.margins: 1
                                id: netAdd
                                height: 27

                                Rectangle {
                                    anchors.fill: parent
                                    color: COMMON.bg2
                                }

                                ParametersNetChoice {
                                    id: netChoice
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    anchors.left: addButton.right
                                    anchors.right: parent.right
                                    anchors.margins: 0
                                    anchors.topMargin: -1
                                    padded: false
                                    model: root.binding.availableNetworks
                                }

                                SIconButton {
                                    id: addButton
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    anchors.left: parent.left
                                    width: height
                                    icon: "qrc:/icons/plus.svg"
                                    color: COMMON.bg4
                                    iconColor: COMMON.bg6

                                    onPressed: {
                                        root.binding.addNetwork(netChoice.currentIndex)
                                    }
                                }
                            }

                            ListView {
                                id: netList
                                anchors.top: netAdd.bottom
                                anchors.bottom: parent.bottom
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.margins:1
                                anchors.topMargin: 0
                                clip: true
                                model: root.binding.activeNetworks

                                boundsBehavior: Flickable.StopAtBounds

                                ScrollBar.vertical: SScrollBarV {
                                    id: scrollBar
                                    policy: netList.contentHeight > netList.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                                }

                                delegate: Item {
                                    width: netList.width
                                    height: 25

                                    property var selected: false

                                    Rectangle {
                                        anchors.fill: parent
                                        color: selected ? COMMON.bg2 : Qt.darker(COMMON.bg2, 1.25) 
                                    }

                                    ParametersNetItem {
                                        anchors.fill: parent
                                        anchors.rightMargin: scrollBar.policy == ScrollBar.AlwaysOn ? 8 : 0
                                        label: modelData.name
                                        type:  modelData.type

                                        onDeactivate: {
                                            root.binding.deleteNetwork(index)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                OColumn {
                    id: ipColumn
                    text: "Inpainting"
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.position(ipColumn)
                    }

                    OSlider {
                        id: strengthInput
                        label: "Strength"
                        width: parent.width
                        height: 30
                        
                        bindMap: root.binding.values
                        bindKey: "strength"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }

                    OChoice {
                        label: "Upscaler"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "img2img_upscaler"
                        bindKeyModel: "img2img_upscalers"

                        popupHeight: root.height + 100

                        property var sr: root.binding.values.get("SRs")

                        function decoration(value) {
                            if(sr.includes(value)) {
                                return "SR"
                            }
                            if(value.startsWith("Latent")) {
                                return "Latent"
                            }
                            return "Pixel"
                        }
                    }
                    OSlider {
                        label: "Padding"
                        width: parent.width
                        height: 30
                        overlay: value == -1

                        bindMap: root.binding.values
                        bindKey: "padding"

                        minValue: -1
                        maxValue: 512
                        precValue: 0
                        incValue: 8
                        snapValue: 16
                        bounded: false
                    }
                    OSlider {
                        label: "Mask Blur"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "mask_blur"

                        minValue: 0
                        maxValue: 10
                        precValue: 0
                        incValue: 1
                        snapValue: 4
                        bounded: false
                    }
                }
                OColumn {
                    id: hrColumn
                    text: "Highres"
                    width: parent.width
                    isCollapsed: true

                    function getHRSize() {
                        if(hrFactorInput.value == 1.0) {
                            return ""
                        }
                        var w = Math.floor((widthInput.value * hrFactorInput.value)/8)*8
                        var h = Math.floor((heightInput.value * hrFactorInput.value)/8)*8
                        return w + "x" + h
                    }

                    input: Item {
                        width: hrColumn.width - 100
                        height: 30
                        clip: true
                        SText {
                            text: hrColumn.getHRSize()
                            anchors.fill: parent
                            color: COMMON.fg2
                            font.pointSize: 9.2
                            opacity: 0.7
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                        }
                    }

                    onExpanded: {
                        paramScroll.position(hrColumn)
                    }

                    OSlider {
                        id: hrFactorInput
                        label: "HR Factor"
                        width: parent.width
                        height: 30

                        overlay: hrFactorInput.value == 1.0

                        bindMap: root.binding.values
                        bindKey: "hr_factor"

                        minValue: 1.0
                        maxValue: 4.0
                        precValue: 2
                        incValue: 0.25
                        snapValue: 0.25
                        bounded: false
                    }
                    OSlider {
                        label: "HR Strength"
                        width: parent.width
                        height: 30

                        disabled: hrFactorInput.value == 1.0

                        bindMap: root.binding.values
                        bindKey: "hr_strength"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }
                    OChoice {
                        label: "HR Upscaler"
                        width: parent.width
                        height: 30

                        disabled: hrFactorInput.value == 1.0

                        bindMap: root.binding.values
                        bindKeyCurrent: "hr_upscaler"
                        bindKeyModel: "hr_upscalers"

                        popupHeight: root.height + 100

                        property var sr: root.binding.values.get("SRs")

                        function decoration(value) {
                            if(sr.includes(value)) {
                                return "SR"
                            }
                            if(value.startsWith("Latent")) {
                                return "Latent"
                            }
                            return "Pixel"
                        }
                    }
                    OSlider {
                        id: hrStepsInput
                        label: "HR Steps"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "hr_steps"

                        disabled: hrFactorInput.value == 1.0
                        overlay: hrFactorInput.value == 1.0 || root.binding.values.get("steps") == hrStepsInput.value
                        defaultValue: root.binding.values.get("steps")

                        minValue: 1
                        maxValue: 100
                        precValue: 0
                        incValue: 1
                        snapValue: 5
                        bounded: false
                    }
                    OChoice {
                        id: hrSamplerInput
                        label: "HR Sampler"
                        width: parent.width
                        height: 30
                        disabled: hrFactorInput.value == 1.0
                        overlay: hrFactorInput.value == 1.0 || root.binding.values.get("sampler") == hrSamplerInput.value
                        bindMap: root.binding.values
                        bindKeyCurrent: "hr_sampler"
                        bindKeyModel: "samplers"
                    }
                    OSlider {
                        visible: !samplerColumn.isCollapsed
                        id: hrEtaInput
                        label: "HR Eta"
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKey: "hr_eta"

                        disabled: hrFactorInput.value == 1.0 || hrSamplerInput.overlay
                        overlay: hrFactorInput.value == 1.0 || root.binding.values.get("eta") == hrEtaInput.value 
                        defaultValue: root.binding.values.get("eta")

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }
                }
                OColumn {
                    id: miscColumn
                    text: "Misc"
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.position(miscColumn)
                    }

                    OSlider {
                        label: "CLIP Skip"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "clip_skip"

                        minValue: 1
                        maxValue: 4
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false
                    }

                    OSlider {
                        label: "Batch Count"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "batch_count"

                        minValue: 1
                        maxValue: 16
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false
                    }

                    OSlider {
                        label: "Batch Size"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "batch_size"

                        minValue: 1
                        maxValue: 8
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false
                    }

                    OChoice {
                        label: "Attention"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "attention"
                        bindKeyModel: "attentions"
                    }

                    OChoice {
                        label: "Device"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "device"
                        bindKeyModel: "devices"

                        onSelected: {
                            GUI.config.set("device", value)
                        }
                    }
                    
                    OSlider {
                        id: subseedStrInput
                        label: "Subseed strength"
                        width: parent.width
                        height: 30
                        overlay: subseedStrInput.value == 0.0
                        
                        bindMap: root.binding.values
                        bindKey: "subseed_strength"

                        minValue: 0
                        maxValue: 0.25
                        precValue: 3
                        incValue: 0.001
                        snapValue: 0.005
                        bounded: false
                    }

                    OTextInput {
                        id: subseedInput
                        label: "Subseed"
                        width: parent.width
                        height: 30
                        disabled: subseedStrInput.overlay

                        bindMap: root.binding.values
                        bindKey: "subseed"

                        validator: IntValidator { 
                            bottom: -1
                            top: 2147483646
                        }
                    }
                }
            }
        }
    }
}