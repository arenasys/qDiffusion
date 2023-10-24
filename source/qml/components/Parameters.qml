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
    property var swap: false
    property var advanced: GUI.config != null ? GUI.config.get("advanced") : false
    property alias button: genButton

    function tr(str, file = "Parameters.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    signal generate()
    signal cancel()
    signal buildModel()
    signal sizeFinished()

    function sizeDrop(mimedata) {
        
    }

    function seedDrop(mimedata) {
        
    }

    property var forever: false
    property var remaining: 0

    property var binding

    Item {
        anchors.top: parent.top
        anchors.left: root.swap ? undefined : parent.left
        anchors.right: root.swap ? parent.right : undefined
        anchors.bottom: parent.bottom

        width: Math.max(150, parent.width)

        GenerateButton {
            id: genButton
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 2
            height: 40

            function sync() {
                genButton.progress = GUI.statusProgress
                genButton.working = GUI.statusMode == 2 || GUI.statusMode == 5
            }

            Timer {
                id: genButtonTimer
                interval: 100
                onTriggered: {
                    genButton.sync()
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
            disabled: (GUI.statusMode != 1 && GUI.statusMode != 2 && GUI.statusMode != 5) || GUI.modelCount == 0
            info: GUI.statusInfo
            remaining: root.remaining

            onPressed: {
                if(GUI.statusMode == 1) {
                    root.generate()
                } else if(GUI.statusMode == 2) {
                    root.cancel()
                }
                genButton.sync()
            }

            onContextMenu: {
                genContextMenu.popup()
            }

            SContextMenu {
                id: genContextMenu
                SContextMenuItem {
                    text: root.tr("Generate Forever")
                    checkable: true
                    onCheckedChanged: {
                        root.forever = checked
                    }
                }
                SContextMenuItem {
                    height: visible ? 20 : 0
                    visible: GUI.statusMode == 2
                    text: root.tr("Cancel")
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
            interactive: false

            ScrollBar.vertical: SScrollBarV {
                id: paramScrollBar
                padding: 0
                barWidth: 2
                stepSize: 1/(paramScroll.contentHeight/40)
                policy: ScrollBar.AlwaysOff
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                onWheel: {
                    if(wheel.angleDelta.y < 0) {
                        paramScrollBar.increase()
                    } else {
                        paramScrollBar.decrease()
                    }
                }
            }

            property var positionTarget: null
            function position(item) {
                var yy = paramColumn.mapFromItem(item, 0, item.height).y
                if(yy > paramScroll.contentY && yy < paramScroll.contentY + paramScroll.height) {
                    return
                }
                if(yy - paramScroll.height < 0) {
                    return
                }
                paramScroll.contentY = yy - paramScroll.height
            }

            function targetPosition(item) {
                positionTarget = item
            }

            onContentHeightChanged: {
                if(positionTarget != null) {
                    position(positionTarget)
                }
            }

            Column {
                id: paramColumn
                width: paramScroll.width
                OColumn {
                    id: optColumn
                    text: root.tr("Options")
                    width: parent.width

                    onExpanded: {
                        paramScroll.targetPosition(optColumn)
                    }

                    OSlider {
                        id: widthInput
                        label: root.tr("Width")
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

                        onFinished: {
                            root.sizeFinished()
                        }

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.sizeDrop(mimeData)
                            }
                        }
                    }
                    OSlider {
                        id: heightInput
                        label: root.tr("Height")
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

                        onFinished: {
                            root.sizeFinished()
                        }

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.sizeDrop(mimeData)
                            }
                        }
                    }
                    OSlider {
                        id: stepsInput
                        label: root.tr("Steps")
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
                        label: root.tr("Scale")
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
                        label: root.tr("Seed")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "seed"

                        validator: RegExpValidator {
                            regExp: /-1||\d{1,10}/
                        }

                        AdvancedDropArea {
                            anchors.fill: parent

                            onDropped: {
                                root.seedDrop(mimeData)
                            }
                        }

                        override: value == "-1" && !active ? "Random" : ""
                    }
                }
                OColumn {
                    id: samplerColumn
                    text: root.tr("Sampler")
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.targetPosition(samplerColumn)
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

                    OChoice {
                        id: scheduleInput
                        label: root.tr("Schedule")
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKeyCurrent: "schedule"
                        bindKeyModel: "schedules"

                        property var last: null

                        onSelected: {
                            if(value != "Default") {
                                last = value
                            } else {
                                last = null
                            }
                        }

                        onOptionsChanged: {
                            if(model != null && last != null) {
                                var idx = model.indexOf(last)
                                if(idx >= 0) {
                                    currentIndex = idx
                                }
                            }
                        }

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OSlider {
                        id: etaInput
                        label: root.tr("Eta")
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
                    text: root.tr("Model")
                    width: parent.width
                    isCollapsed: true

                    property var componentMode: unetInput.value != vaeInput.value || unetInput.value != clipInput.value

                    onExpanded: {
                        paramScroll.targetPosition(modelColumn)
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

                        function display(text) {
                            return GUI.modelName(text)
                        }

                        function filterModel(model) {
                            if(model) {
                                return GUI.filterFavourites(model)
                            } else {
                                return []
                            }
                        }

                        Connections {
                            target: GUI
                            function onFavUpdated() {
                                modelInput.doUpdate()
                            }
                        }

                        onSelected: {
                            root.binding.values.set("VAE", value)
                            root.binding.values.set("UNET", value)
                            root.binding.values.set("CLIP", value)
                        }

                        onContextMenu: {
                            modelsContextMenu.popup()
                        }
                    }

                    property var models: root.binding.values.get("models")

                    OChoice {
                        id: unetInput
                        label: root.tr("UNET")
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKeyCurrent: "UNET"
                        bindKeyModel: "UNETs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return root.tr("External")
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }

                        onSelected: {
                            root.binding.values.set("model", value)
                        }
                    }
                    OChoice {
                        id: vaeInput
                        label: root.tr("VAE")
                        width: parent.width
                        height: 25

                        bindMap: root.binding.values
                        bindKeyCurrent: "VAE"
                        bindKeyModel: "VAEs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return root.tr("External")
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }
                    OChoice {
                        id: clipInput
                        label: root.tr("CLIP")
                        width: parent.width
                        height: 25

                        bindMap: root.binding.values
                        bindKeyCurrent: "CLIP"
                        bindKeyModel: "CLIPs"

                        overlay: !modelColumn.componentMode
                        popupHeight: root.height + 100

                        function decoration(value) {
                            if(!modelColumn.models.includes(value)) {
                                return root.tr("External")
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }
                }

                OColumn {
                    id: netColumn
                    text: root.tr("Networks")
                    width: parent.width
                    padding: false
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.targetPosition(netColumn)
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

                                OChoice {
                                    id: netChoice
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    anchors.left: addButton.right
                                    anchors.right: parent.right
                                    anchors.margins: 0
                                    anchors.topMargin: -1
                                    padded: false
                                    label: ""

                                    model: GUI.filterFavourites(root.binding.availableNetworks)

                                    Connections {
                                        target: GUI
                                        function onFavUpdated() {
                                            netChoice.model = GUI.filterFavourites(root.binding.availableNetworks)
                                        }
                                    }

                                    function decoration(text) {
                                        return GUI.netType(text)
                                    }

                                    function display(text) {
                                        return GUI.modelName(text)
                                    }
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
                                        root.binding.addNetwork(netChoice.model[netChoice.currentIndex])
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
                                        label: GUI.modelName(modelData)
                                        type: GUI.netType(modelData)

                                        onDeactivate: {
                                            root.binding.deleteNetwork(index)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    OChoice {
                        label: root.tr("Mode")
                        width: parent.width
                        bottomPadded: true
                        height: 23

                        bindMap: root.binding.values
                        bindKeyCurrent: "network_mode"
                        bindKeyModel: "network_modes"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }
                }
                OColumn {
                    id: ipColumn
                    text: root.tr("Inpainting")
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.targetPosition(ipColumn)
                    }

                    OSlider {
                        id: strengthInput
                        label: root.tr("Strength")
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
                        label: root.tr("Upscaler")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "img2img_upscaler"
                        bindKeyModel: "img2img_upscalers"

                        popupHeight: root.height + 100

                        property var sr: root.binding.values.get("SRs")

                        function filterModel(model) {
                            if(model) {
                                return model.filter(u => !u.includes("Latent"));
                            } else {
                                return []
                            }
                        }

                        function decoration(value) {
                            if(sr.includes(value)) {
                                return root.tr("SR")
                            }
                            if(value.startsWith("Latent")) {
                                return root.tr("Latent")
                            }
                            return root.tr("Pixel")
                        }

                        function display(text) {
                            return root.tr(GUI.modelName(text), "Options")
                        }
                    }
                    OSlider {
                        id: paddingInput
                        label: root.tr("Padding")
                        width: parent.width
                        height: 30
                        overlay: value == -1 && !paddingInput.active

                        bindMap: root.binding.values
                        bindKey: "padding"

                        minValue: -1
                        maxValue: 512
                        precValue: 0
                        incValue: 8
                        snapValue: 16
                        bounded: false

                        override: value == "-1" && !active ? "Full" : ""
                    }

                    OSlider {
                        label: root.tr("Mask Blur")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "mask_blur"

                        minValue: 0
                        maxValue: 10
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false
                    }

                    OSlider {
                        label: root.tr("Mask Expand")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "mask_expand"

                        minValue: 0
                        maxValue: 10
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false
                    }

                    OChoice {
                        label: root.tr("Mask Fill")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "mask_fill"
                        bindKeyModel: "mask_fill_modes"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }
                }
                OColumn {
                    id: hrColumn
                    text: root.tr("Highres")
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
                            pointSize: 9.2
                            opacity: 0.7
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                        }
                    }

                    onExpanded: {
                        paramScroll.targetPosition(hrColumn)
                    }

                    OSlider {
                        id: hrFactorInput
                        label: root.tr("HR Factor")
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
                        label: root.tr("HR Strength")
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
                        label: root.tr("HR Upscaler")
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
                                return root.tr("SR")
                            }
                            if(value.startsWith("Latent")) {
                                return root.tr("Latent")
                            }
                            return root.tr("Pixel")
                        }

                        function display(text) {
                            return root.tr(GUI.modelName(text), "Options")
                        }
                    }
                    OSlider {
                        visible: root.advanced
                        label: root.tr("HR ToMe Ratio")
                        width: parent.width
                        height: 30

                        disabled: hrFactorInput.value == 1.0
                        overlay: value == 0.0

                        bindMap: root.binding.values
                        bindKey: "hr_tome_ratio"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }
                    OSlider {
                        id: hrStepsInput
                        label: root.tr("HR Steps")
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
                        visible: root.advanced
                        id: hrSamplerInput
                        label: root.tr("HR Sampler")
                        width: parent.width
                        height: 30
                        disabled: hrFactorInput.value == 1.0
                        overlay: hrFactorInput.value == 1.0 || root.binding.values.get("true_sampler") == hrSamplerInput.value
                        bindMap: root.binding.values
                        bindKeyCurrent: "hr_sampler"
                        bindKeyModel: "true_samplers"
                    }
                    OSlider {
                        visible: !samplerColumn.isCollapsed && root.advanced
                        id: hrEtaInput
                        label: root.tr("HR Eta")
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
                    text: root.tr("Misc")
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.targetPosition(miscColumn)
                    }

                    OSlider {
                        label: root.tr("CLIP Skip")
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
                        label: root.tr("Batch Count")
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
                        label: root.tr("Batch Size")
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
                        visible: root.advanced
                        label: root.tr("Prediction")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "prediction_type"
                        bindKeyModel: "prediction_types"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }
                    
                    OSlider {
                        visible: root.advanced
                        label: root.tr("CFG Rescale")
                        width: parent.width
                        height: 30

                        overlay: value == 0.0

                        bindMap: root.binding.values
                        bindKey: "cfg_rescale"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }

                    OSlider {
                        visible: root.advanced
                        label: root.tr("ToMe Ratio")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "tome_ratio"

                        overlay: value == 0.0

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }

                    OSlider {
                        id: subseedStrInput
                        label: root.tr("Subseed strength")
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
                        label: root.tr("Subseed")
                        width: parent.width
                        height: 30
                        disabled: subseedStrInput.overlay

                        bindMap: root.binding.values
                        bindKey: "subseed"

                        validator: IntValidator { 
                            bottom: -1
                            top: 2147483646
                        }

                        override: value == "-1" && !active ? "Random" : ""
                    }
                }
                OColumn {
                    id: opColumn
                    text: root.tr("Operation")
                    width: parent.width
                    isCollapsed: true

                    onExpanded: {
                        paramScroll.targetPosition(opColumn)
                    }

                    OChoice {
                        label: root.tr("Preview")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "preview_mode"
                        bindKeyModel: "preview_modes"

                        onSelected: {
                            GUI.config.set("previews", value)
                        }

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OSlider {
                        label: root.tr("Preview interval")
                        width: parent.width
                        height: 30
                        
                        bindMap: root.binding.values
                        bindKey: "preview_interval"

                        minValue: 1
                        maxValue: 10
                        precValue: 0
                        incValue: 1
                        snapValue: 1

                        onSelected: {
                            GUI.config.set("preview_interval", value)
                        }
                    }

                    OChoice {
                        label: root.tr("Artifacts")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "artifact_mode"
                        bindKeyModel: "artifact_modes"

                        onSelected: {
                            GUI.config.set("artifacts", value)
                        }

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OChoice {
                        label: root.tr("VRAM")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "vram_mode"
                        bindKeyModel: "vram_modes"

                        onSelected: {
                            GUI.config.set("vram", value)
                        }

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OChoice {
                        label: root.tr("Attention")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "attention"
                        bindKeyModel: "attentions"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OChoice {
                        visible: root.advanced
                        label: root.tr("VAE Tiling")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "tiling_mode"
                        bindKeyModel: "tiling_modes"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OChoice {
                        visible: root.advanced
                        label: root.tr("Autocast")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "autocast"
                        bindKeyModel: "autocast_modes"

                        function display(text) {
                            return root.tr(text, "Options")
                        }
                    }

                    OChoice {
                        label: root.tr("Device")
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "device"
                        bindKeyModel: "devices"

                        onSelected: {
                            GUI.config.set("device", value)
                        }
                    }

                    OTextInput {
                        label: root.tr("Output Folder")
                        width: parent.width
                        height: 30
                        placeholder: root.tr("Default", "Options")

                        bindMap: root.binding.values
                        bindKey: "output_folder"
                    }
                }
            }
        }
    }
}