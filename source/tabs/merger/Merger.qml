import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

import gui 1.0

import "../../style"
import "../../components"

Rectangle {
    id: root
    clip: true

    color: COMMON.bg0_5

    property var operation: MERGER.selectedOperation

    function tr(str, file = "Merger.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    SDialog {
        id: buildDialog
        title: root.tr("Build model")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        dim: true

        onOpened: {
            filenameInput.value = MERGER.recipeName()
        }

        OTextInput {
            id: filenameInput
            width: buildDialog.width - 10
            height: 30
            label: root.tr("Filename")
            value: ""
        }

        width: root.width / 2
        height: 87

        onAccepted: {
            MERGER.buildModel(filenameInput.value)
        }
    }

    Item {
        anchors.right: divider.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: Math.max(divider.x, 330)

        SShadow {
            color: COMMON.bg0
            anchors.fill: parent
        }

        Flickable {
            id: flickable
            anchors.fill: parent
            contentHeight: operationsColumn.height + optionsColumn.height + (advancedColumn.visible ? advancedColumn.height + 10 : 0) + 60
            contentWidth: width
            boundsBehavior: Flickable.StopAtBounds
            clip: true
            interactive: false

            ScrollBar.vertical: SScrollBarV {
                id: scrollBar
                policy: flickable.contentHeight > flickable.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                onWheel: {
                    if(wheel.angleDelta.y < 0) {
                        scrollBar.increase()
                    } else {
                        scrollBar.decrease()
                    }
                }
            }

            Rectangle {
                anchors.fill: operationsColumn
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }

            Column {
                id: operationsColumn
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                width: parent.width - 20

                Item {
                    width: parent.width
                    height: 30
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 2
                        anchors.bottomMargin: 0

                        color: COMMON.bg2_5
                    }
                    SText {
                        text: "Operations"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        font.pointSize: 10.5
                        color: COMMON.fg1
                    }

                    SIconButton {
                        id: addButton
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 1
                        anchors.topMargin: 2
                        anchors.rightMargin: 5
                        color: "transparent"
                        height: 23
                        width: 23
                        tooltip: root.tr("Add operation")
                        icon: "qrc:/icons/plus.svg"
                        onPressed: {
                            MERGER.addOperation()
                        }
                    }
                }

                Item {
                    width: parent.width
                    height: 2

                    Rectangle {
                        id: sideBar
                        color: COMMON.bg6
                        x: -8
                        y: 0
                        width: 6
                        height: operationList.height - y + 35 + 30
                    }
                }

                ListView {
                    id: operationList
                    model: MERGER.operations
                    x: 10
                    width: parent.width - 20
                    height: contentHeight
                    
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: SScrollBarV {
                        policy: operationList.contentHeight > operationList.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                    }

                    delegate: Rectangle {
                        height: 25
                        width: parent.width
                        color: selected ? COMMON.bg2 : COMMON.bg0

                        property var modelNumber: operationText.text == "Add Difference" ? 3 : 2
                        property var modelSize:  Math.max(100, (width - 125) / modelNumber)
                        property var selected: MERGER.selectedOperationIndex == index

                        Rectangle {
                            visible: selected
                            color: COMMON.bg6
                            width: 12
                            height: 6
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.left

                            function sync() {
                                if(selected) {
                                    sideBar.y = (index * 25) + 12
                                }
                            }

                            onVisibleChanged: {
                                sync()
                            }

                            Component.onCompleted: {
                                sync()
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onPressed: {
                                MERGER.selectedOperationIndex = index
                                if (mouse.button & Qt.RightButton) {
                                    opContextMenu.popup()
                                }
                            }
                        }

                        SContextMenu {
                            id: opContextMenu
                            SContextMenuItem {
                                height: 20
                                text: root.tr("Delete")
                                onPressed: {
                                    MERGER.deleteOperation()
                                }
                            }
                        }

                        Row {
                            clip: true
                            anchors.fill: parent

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: selected ? COMMON.bg5 : COMMON.bg4
                            }

                            Rectangle {
                                height: parent.height
                                width: 23
                                color: selected ? COMMON.bg2 : COMMON.bg0
                                SText {
                                    text: index
                                    width: 24
                                    height: parent.height
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                    font.pointSize: 9.8
                                    color: COMMON.fg2
                                    opacity: 0.8
                                    monospace: true
                                }
                            }

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            Rectangle {
                                height: parent.height
                                width: 99
                                color: selected ? COMMON.bg3 : COMMON.bg0

                                OText {
                                    id: operationText
                                    width: 99
                                    height: parent.height
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                    font.pointSize: 9.4
                                    color: COMMON.fg1

                                    bindMap: modelData.parameters
                                    bindKey: "operation"
                                }
                            }

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            OText {
                                width: modelSize - 1
                                height: parent.height
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pointSize: 9.4
                                color: COMMON.fg1_5
                                elide: Text.ElideRight
                                leftPadding: 3
                                rightPadding: 3

                                bindMap: modelData.parameters
                                bindKey: "model_a"

                                function display(text) {
                                    if(text == "") {
                                        return "None"
                                    }
                                    return GUI.modelName(text)
                                }
                            }

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            OText {
                                width: modelSize - 1
                                height: parent.height
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pointSize: 9.4
                                color: COMMON.fg1_5
                                elide: Text.ElideRight
                                leftPadding: 3
                                rightPadding: 3

                                bindMap: modelData.parameters
                                bindKey: "model_b"

                                function display(text) {
                                    if(text == "") {
                                        return "None"
                                    }
                                    return GUI.modelName(text)
                                }
                            }

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            OText {
                                id: modelC
                                visible: width != 0
                                width: text != "" ? modelSize - 1 : 0
                                height: parent.height
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pointSize: 9.4
                                color: COMMON.fg1_5
                                elide: Text.ElideRight
                                leftPadding: 3
                                rightPadding: 3

                                bindMap: modelData.parameters
                                bindKey: "model_c"

                                function display(text) {
                                    if(text == "") {
                                        return "None"
                                    }
                                    return GUI.modelName(text)
                                }
                            }
                        }

                        Rectangle {
                            anchors.bottom: parent.bottom
                            width: parent.width
                            height: 1
                            color: COMMON.bg4
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: COMMON.bg4
                        border.width: 1
                    }
                }

                Item {
                    width: parent.width
                    height: 4
                }
            }

            Item {
                height: 0
                width: parent.width
                Rectangle {
                    x: 2
                    y: optionsColumn.y + 13
                    width: optionsColumn.x
                    height: 6
                    color: COMMON.bg6
                }
            }

            Rectangle {
                anchors.top: operationsColumn.bottom
                anchors.topMargin: -2
                height: 32
                anchors.left: operationsColumn.left
                anchors.leftMargin: 20
                width: 200
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2

                Row {
                    anchors.fill: parent
                    anchors.margins: 3
                    SButton {
                        label: "Build"
                        disabled: !MERGER.valid
                        width: parent.width/3
                        height: parent.height
                        onPressed: {
                            buildDialog.open()
                        }
                    }
                    SButton {
                        label: "Save"
                        disabled: !MERGER.valid
                        width: parent.width/3
                        height: parent.height
                        onPressed: {
                            saveFileDialog.currentFile = MERGER.recipeJSONName()
                            saveFileDialog.open()
                        }
                    }
                    SButton {
                        label: "Load"
                        width: parent.width/3
                        height: parent.height
                        onPressed: {
                            loadFileDialog.open()
                        }
                    }

                    FileDialog {
                        id: loadFileDialog
                        nameFilters: [root.tr("Recipe files") + " (*.json)"]

                        onAccepted: {
                            MERGER.loadRecipe(file)
                        }
                    }

                    FileDialog {
                        id: saveFileDialog
                        nameFilters: [root.tr("Recipe files") + " (*.json)"]
                        fileMode: FileDialog.SaveFile
                        defaultSuffix: "json"
                        onAccepted: {
                            MERGER.saveRecipe(file)
                        }
                    }
                }
            }

            Rectangle {
                anchors.top: operationsColumn.bottom
                anchors.topMargin: -2
                height: 32
                anchors.right: operationsColumn.right
                anchors.rightMargin: 20
                width: Math.min(200, operationsColumn.width - 260)
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2

                Row {
                    anchors.fill: parent
                    anchors.margins: 3
                    OChoice {
                        id: typeChoice
                        label: "Type"
                        width: parent.width
                        height: parent.height - 2
                        
                        property var key: value == "Checkpoint" ? "models" : "LoRAs"

                        bindMap: MERGER.parameters
                        bindKeyCurrent: "type"
                        bindKeyModel: "types"
                    }
                }
            }

            Column {
                id: optionsColumn
                clip: true
                anchors.top: operationsColumn.bottom
                anchors.topMargin: 10 + 32
                anchors.right: parent.right
                anchors.rightMargin: Math.max(10, (parent.width - width)/2)
                width: 250

                Rectangle {
                    width: parent.width
                    height: 30
                    color: COMMON.bg2_5
                    SText {
                        text: "Options"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        font.pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OChoice {
                        id: operationChoice
                        height: 30
                        width: parent.width
                        label: "Operation"
                        
                        bindMap: root.operation.parameters

                        bindKeyCurrent: "operation"
                        bindKeyModel: typeChoice.value == "Checkpoint" ? "operations_checkpoint" : "operations_lora"
                    }

                    OChoice {
                        id: modeChoice
                        height: 30
                        width: parent.width
                        label: "Mode"

                        bindMap: root.operation.parameters
                        bindKeyCurrent: "mode"
                        bindKeyModel: "modes"
                    }
                }

                Item {
                    width: parent.width
                    height: 2
                }

                Rectangle {
                    color: COMMON.bg4
                    width: parent.width
                    height: 2
                }

                Rectangle {
                    width: parent.width
                    height: 30
                    color: COMMON.bg2_5
                    SText {
                        text: "Models"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        font.pointSize: 10.5
                        color: COMMON.fg1
                    }


                    SText {
                        text: {
                            if(operationChoice.value == "Weighted Sum") {
                                return "αA + (1-α)B"
                            }
                            if(operationChoice.value == "Add Difference") {
                                return "A + α(B - C)"
                            }
                            if(operationChoice.value == "Insert LoRA") {
                                return "A + αB"
                            }
                            if(operationChoice.value == "Extract LoRA") {
                                return "α(A - B)"
                            }
                            return ""
                        }
                        
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignRight
                        rightPadding: 10
                        bottomPadding: 2
                        font.pointSize: 9.8
                        color: COMMON.fg1_5
                    }

                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OChoice {
                        height: 30
                        width: parent.width
                        label: (bindKeyModel == "models" ? "Model" : "LoRA") + " A"
                        
                        bindMapCurrent: root.operation.parameters
                        bindKeyCurrent: "model_a"
                        bindMapModel: BASIC.parameters.values
                        bindKeyModel: root.operation.modelAMap
                        
                        emptyValue: "None"

                        function expandModel(model) {
                            if(bindKeyModel == typeChoice.key) {
                                return root.operation.availableResults.concat(model)
                            }
                            return model
                        }

                        function decoration(text) {
                            if(text.startsWith("_result_")) {
                                return "Result"
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }

                    OChoice {
                        height: 30
                        width: parent.width
                        label: (bindKeyModel == "models" ? "Model" : "LoRA") + " B"

                        bindMapCurrent: root.operation.parameters
                        bindKeyCurrent: "model_b"
                        bindMapModel: BASIC.parameters.values
                        bindKeyModel: root.operation.modelBMap

                        emptyValue: "None"

                        function expandModel(model) {
                            if(bindKeyModel == typeChoice.key) {
                                return root.operation.availableResults.concat(model)
                            }
                            return model
                        }

                        function decoration(text) {
                            if(text.startsWith("_result_")) {
                                return "Result"
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }

                    OChoice {
                        visible: height != 0
                        height: operationChoice.value == "Add Difference" ? 30 : 0
                        width: parent.width
                        label: (bindKeyModel == "models" ? "Model" : "LoRA") + " C"

                        bindMapCurrent: root.operation.parameters
                        bindKeyCurrent: "model_c"
                        bindMapModel: BASIC.parameters.values
                        bindKeyModel: root.operation.modelCMap

                        emptyValue: "None"

                        function expandModel(model) {
                            if(bindKeyModel == typeChoice.key) {
                                return root.operation.availableResults.concat(model)
                            }
                            return model
                        }

                        function decoration(text) {
                            if(text.startsWith("_result_")) {
                                return "Result"
                            }
                            return ""
                        }

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }
                }

                Item {
                    width: parent.width
                    height: 2
                }

                Rectangle {
                    color: COMMON.bg4
                    width: parent.width
                    height: 2
                }

                Rectangle {
                    width: parent.width
                    height: 30
                    color: COMMON.bg2_5
                    SText {
                        text: "Parameters"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        font.pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    property var mode: operationChoice.value == "Insert LoRA" ? "LoRA" : typeChoice.value
                    property var hide_rank: operationChoice.value == "Insert LoRA"

                    OSlider {
                        visible: height != 0
                        height: modeChoice.value == "Advanced" ? 0 : 30
                        width: parent.width
                        label: "Alpha (α)"
                        
                        bindMap: root.operation.parameters
                        bindKey: "alpha"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }

                    OSlider {
                        visible: height != 0
                        height: 30
                        width: parent.width
                        label: "CLIP Alpha (α)"
                        
                        bindMap: root.operation.parameters
                        bindKey: "clip_alpha"

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05
                    }

                    OSlider {
                        visible: height != 0
                        height: (parent.mode == "LoRA" && !parent.hide_rank) ? 30 : 0
                        width: parent.width
                        label: "LoRA Rank"
                        
                        bindMap: root.operation.parameters
                        bindKey: "rank"

                        minValue: 8
                        maxValue: 256
                        precValue: 0
                        incValue: 8
                        snapValue: 8
                    }

                    OSlider {
                        visible: height != 0
                        height: (parent.mode == "LoRA" && !parent.hide_rank) ? 30 : 0
                        width: parent.width
                        label: "LoCon Rank"
                        
                        bindMap: root.operation.parameters
                        bindKey: "conv_rank"

                        minValue: 8
                        maxValue: 256
                        precValue: 0
                        incValue: 8
                        snapValue: 8
                    }

                    OChoice {
                        visible: height != 0
                        height: parent.mode == "Checkpoint" ? 30 : 0
                        width: parent.width
                        label: "VAE Source"

                        bindMap: root.operation.parameters
                        bindKeyCurrent: "vae_source"
                        bindKeyModel: "sources"
                    }
                }

                Item {
                    width: parent.width
                    height: 4
                }
            }

            Rectangle {
                id: advancedColumn
                anchors.top: optionsColumn.bottom
                anchors.topMargin: 10
                anchors.right: parent.right
                anchors.rightMargin: Math.max(10, (parent.width - width)/2)
                width: blockWeightLabels.big ? parent.width - 20 : 350

                height: blockWeightLabels.big ? 396 : 306
                visible: modeChoice.value == "Advanced"

                Rectangle {
                    width: 6
                    height: 10
                    anchors.bottom: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: COMMON.bg6
                }

                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2

                Item {
                    anchors.fill: parent
                    anchors.margins: 2
                    Rectangle {
                        id: advancedHeader
                        width: parent.width
                        height: 30
                        color: COMMON.bg2_5
                        SText {
                            text: "Advanced (α)"
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 10
                            bottomPadding: 2
                            font.weight: Font.Medium
                            font.pointSize: 10.5
                            color: COMMON.fg1
                        }
                    }

                    Row {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: advancedHeader.bottom
                        anchors.bottom: parent.bottom

                        ListView {
                            height: parent.height
                            width: blockWeightLabels.big ? parent.width / 3 : parent.width / 2
                            model: {
                                if(blockWeightLabels.value == "12 Block") {
                                    return ["IN00","IN01","IN02","IN03","IN04","IN05","IN06","IN07","IN08","IN09","IN10","IN11"]
                                } else {
                                    return ["DOWN0","DOWN1","DOWN2","DOWN3", "MID", "UP0", "UP1", "UP2", "UP3"]
                                }
                            }

                            delegate: Item {
                                width: parent.width
                                height: 30
                                OSlider {
                                    anchors.fill: parent
                                    label: modelData

                                    bindMap: root.operation.blockWeights
                                    bindKey: modelData

                                    minValue: 0
                                    maxValue: 1
                                    precValue: 2
                                    incValue: 0.01
                                    snapValue: 0.01

                                    onSelected: {
                                        blockWeightPresets.clear()
                                    }
                                }
                            }
                        }

                        Item {
                            height: parent.height
                            width: blockWeightLabels.big ? parent.width / 3 : parent.width / 2

                            OChoice {
                                id: blockWeightLabels
                                anchors.top: parent.top
                                width: parent.width
                                height: 30
                                label: "Labels"
                                property var big: value == "12 Block"

                                bindMap: root.operation.parameters
                                bindKeyModel: "labels"
                                bindKeyCurrent: "label"

                                emptyValue: "None"
                            }

                            Item {
                                id: blockWeightValues
                                anchors.top: blockWeightLabels.bottom
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.margins: 2
                                height: 208

                                Rectangle {
                                    width: parent.width
                                    height: 30
                                    color: COMMON.bg2_5
                                    SText {
                                        text: "Values"
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 10
                                        topPadding: 1
                                        font.weight: Font.Medium
                                        font.pointSize: 10.5
                                        color: COMMON.fg1
                                    }
                                }

                                Rectangle {
                                    anchors.fill: valueArea
                                    color: COMMON.bg1
                                }

                                STextArea {
                                    id: valueArea
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    anchors.topMargin: 32
                                    anchors.bottomMargin: 27
                                    font.pointSize: 9.5
                                    area.color: COMMON.fg1_5

                                    property var syncing: true

                                    property var source: root.operation

                                    onInput: {
                                        syncing = false
                                    }

                                    function sync() {
                                        syncing = true
                                        text = root.operation.getBlockWeightValues()
                                    }

                                    onSourceChanged: {
                                        if(syncing) {
                                            sync()
                                        }
                                    }

                                    Connections {
                                        target: root.operation.blockWeights
                                        function onUpdated() {
                                            if(valueArea.syncing) {
                                                valueArea.sync()
                                            }
                                        }
                                    }

                                    Connections {
                                        target: root.operation.parameters
                                        function onUpdated() {
                                            if(valueArea.syncing) {
                                                valueArea.sync()
                                            }
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        color: 'transparent'
                                        border.color: COMMON.bg4
                                        border.width: 1
                                    }
                                }

                                SButton {
                                    anchors.left: parent.left
                                    anchors.bottom: parent.bottom
                                    label: "Apply"
                                    disabled: valueArea.syncing
                                    width: (parent.width / 2) - 1
                                    height: 25
                                    anchors.leftMargin: 2
                                    anchors.bottomMargin: 2

                                    onPressed: {
                                        root.operation.setBlockWeightValues(valueArea.text)
                                        root.operation.parameters.set("preset", "None")
                                        valueArea.sync()
                                    }
                                }

                                SButton {
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    label: "Revert"
                                    disabled: valueArea.syncing
                                    width: (parent.width / 2) - 1
                                    height: 25
                                    anchors.rightMargin: 2
                                    anchors.bottomMargin: 2

                                    onPressed: {
                                        valueArea.sync()
                                    }

                                }

                                Rectangle {
                                    anchors.fill: parent
                                    color: 'transparent'
                                    border.color: COMMON.bg4
                                    border.width: 2
                                }
                            }

                            OChoice {
                                id: blockWeightPresets
                                anchors.top: blockWeightValues.bottom
                                width: parent.width
                                height: 30
                                label: "Preset"

                                bindMap: root.operation.parameters
                                bindKeyModel: "presets"
                                bindKeyCurrent: "preset"

                                emptyValue: "None"

                                function clear() {
                                    root.operation.setBlockWeightPreset("None")
                                }

                                onValueChanged: {
                                    root.operation.setBlockWeightPreset(value)
                                }
                            }

                            

                            OSlider {
                                anchors.bottom: parent.bottom
                                anchors.margins: 2
                                visible: blockWeightLabels.big
                                width: visible ? parent.width : 0
                                height: visible ? 30 : 0
                                label: "M00"

                                bindMap: root.operation.blockWeights
                                bindKey: label

                                minValue: 0
                                maxValue: 1
                                precValue: 2
                                incValue: 0.01
                                snapValue: 0.01

                                onSelected: {
                                    blockWeightPresets.clear()
                                }
                            }
                        }

                        ListView {
                            visible: blockWeightLabels.big
                            height: visible ? parent.height : 0
                            width: visible ? parent.width / 3 : 0
                            model: ["OUT00","OUT01","OUT02","OUT03","OUT04","OUT05","OUT06","OUT07","OUT08","OUT09","OUT10","OUT11"].reverse()

                            delegate: Item {
                                width: parent != null ? parent.width : 0
                                height: 30
                                OSlider {
                                    anchors.fill: parent
                                    label: modelData
                                    
                                    bindMap: root.operation.blockWeights
                                    bindKey: modelData

                                    minValue: 0
                                    maxValue: 1
                                    precValue: 2
                                    incValue: 0.01
                                    snapValue: 0.01

                                    onSelected: {
                                        blockWeightPresets.clear()
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.fill: optionsColumn
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }
        }
    }

    Item {
        anchors.left: divider.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: Math.max(parent.width-(divider.x+5), 330)
        clip: true

        SShadow {
            opacity: 0.7
            anchors.fill: parent
        }

        Item {
            anchors.top: genButtonBox.bottom
            anchors.bottom: resultDivider.top
            anchors.left: parent.left
            anchors.right: parent.right
            id: resultArea

            property var current: MERGER.outputs(MERGER.openedIndex)
            onCurrentChanged: {
                if(current != null) {
                    bg.image = Qt.binding(function () { return current.display; })
                    bg.visible = true
                } else {
                    bg.image = bg.clear()
                    bg.visible = false
                }
            }

            Item {
                anchors.fill: parent
                clip: true

                SShadow {
                    anchors.fill: parent
                }

                Image {
                    id: placeholder
                    visible: movable.itemWidth == 0
                    source: "qrc:/icons/placeholder_black.svg"
                    height: 50
                    width: height
                    sourceSize: Qt.size(width*1.25, height*1.25)
                    anchors.centerIn: parent
                }

                ColorOverlay {
                    visible: placeholder.visible
                    anchors.fill: placeholder
                    source: placeholder
                    color: COMMON.bg4
                }

                MovableItem {
                    id: movable
                    anchors.fill: parent
                    anchors.margins: 10

                    clip: false
                    itemWidth: 0
                    itemHeight: 0

                    Item {
                        id: item
                        x: Math.floor(parent.item.x)
                        y: Math.floor(parent.item.y)
                        width: Math.ceil(parent.item.width)
                        height: Math.ceil(parent.item.height)
                    }

                    SGlow {
                        visible: movable.item.width > 0
                        target: movable.item
                    }

                    ImageDisplay {
                        onImageChanged: {
                            movable.itemWidth = resultArea.current != null ? resultArea.current.width : 0
                            movable.itemHeight = resultArea.current != null ? resultArea.current.height : 0
                        }
                        id: bg
                        anchors.fill: item
                        smooth: implicitWidth*1.25 < width && implicitHeight*1.25 < height ? false : true
                    }
                }
            }
        }

        Rectangle {
            id: genButtonBox
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: -2
            width: 200
            height: 48
            clip: true

            color: "transparent"
            border.color: COMMON.bg4
            border.width: 2

            RectangularGlow {
                anchors.fill: genButton
                glowRadius: 8
                opacity: 0.4
                spread: 0.1
                color: "black"
                cornerRadius: 10
            }


            GenerateButton {
                id: genButton
                anchors.top: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
                width: 200
                anchors.margins: 4
                height: 40
                text: "Preview"

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
                disabled: (GUI.statusMode != 1 && GUI.statusMode != 2) || GUI.modelCount == 0 || !MERGER.valid
                info: GUI.statusInfo

                onPressed: {
                    if(GUI.statusMode == 1) {
                        MERGER.generate()
                    }
                    if(GUI.statusMode == 2) {
                        MERGER.cancel()
                    }
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
                            MERGER.forever = checked
                        }
                    }
                    SContextMenuItem {
                        height: visible ? 20 : 0
                        visible: GUI.statusMode == 2
                        text: root.tr("Cancel")
                        onPressed: {
                            MERGER.cancel()
                        }
                    }
                }
            }
        }

        Item {
            id: results
            anchors.top: resultDivider.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.topMargin: -1

            ListView {
                id: listView
                interactive: false
                boundsBehavior: Flickable.StopAtBounds
                displayMarginBeginning: 1
                displayMarginEnd: 1
                clip: true
                orientation: Qt.Horizontal
                width: Math.min(contentWidth, parent.width)
                height: parent.height

                model: Sql {
                    id: outputsSql
                    query: "SELECT id FROM merge_outputs ORDER BY id DESC;"
                }

                ScrollBar.horizontal: SScrollBarH { 
                    id: scrollBarResults
                    stepSize: 1/(4*Math.ceil(outputsSql.length))
                    policy: listView.contentWidth > listView.width ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton
                    z: -1
                    onWheel: {
                        if(wheel.angleDelta.y < 0) {
                            scrollBarResults.increase()
                        } else {
                            scrollBarResults.decrease()
                        }
                    }
                }

                delegate: Item {
                    id: item
                    height: Math.floor(listView.height)
                    width: height-9
                    property var modelObj: MERGER.outputs(sql_id)
                    property var selected: MERGER.openedIndex == sql_id

                    onSelectedChanged: {
                        if(selected) {
                            listView.positionViewAtIndex(index, ListView.Contain)
                        }
                    }

                    Connections {
                        target: MERGER
                        function onInput() {
                            if(selected) {
                                itemFrame.forceActiveFocus()
                            }
                        }
                    }

                    Rectangle {
                        id: itemFrame
                        anchors.fill: parent
                        anchors.margins: 9
                        anchors.leftMargin: 0
                        color: COMMON.bg00
                        clip: true

                        property var highlight: selected || contextMenu.opened

                        RectangularGlow {
                            anchors.fill: trueFrame
                            glowRadius: 5
                            opacity: 0.4
                            spread: 0.2
                            color: "black"
                            cornerRadius: 10
                        }

                        TransparencyShader {
                            anchors.fill: trueFrame
                        }

                        ImageDisplay {
                            id: itemImage
                            visible: !modelObj.empty
                            anchors.fill: parent
                            image: modelObj.display
                            centered: true
                            smooth: implicitWidth > trueWidth && implicitHeight > trueHeight
                        }
                        
                        Item {
                            id: trueFrame
                            x: itemImage.trueX
                            y: itemImage.trueY
                            width: itemImage.trueWidth
                            height: itemImage.trueHeight

                            Rectangle {
                                visible: sizeLabel.text != ""
                                anchors.fill: sizeLabel
                                color: "#e0101010"
                                border.width: 1
                                border.color: COMMON.bg3
                            }

                            SText {
                                id: sizeLabel
                                text: itemImage.implicitWidth + "x" + itemImage.implicitHeight
                                anchors.top: parent.top
                                anchors.right: parent.right
                                leftPadding: 3
                                topPadding: 3
                                rightPadding: 3
                                bottomPadding: 3
                                color: COMMON.fg1_5
                                font.pointSize: 9.2
                            }

                            Rectangle {
                                anchors.fill: parent
                                border.color: itemFrame.highlight ? COMMON.fg2 : COMMON.bg4
                                border.width: 1
                                color: "transparent"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            property var startPosition: Qt.point(0,0)
                            onPressed: {
                                if (mouse.button == Qt.LeftButton) {
                                    listView.currentIndex = index
                                    itemFrame.forceActiveFocus()
                                    startPosition = Qt.point(mouse.x, mouse.y)
                                    MERGER.openedIndex = sql_id
                                }
                                if (mouse.button == Qt.RightButton && modelObj.ready) {
                                    contextMenu.popup()
                                }
                            }

                            onPositionChanged: {
                                if(pressedButtons & Qt.LeftButton) {
                                    var delta = Qt.point(mouse.x-startPosition.x, mouse.y-startPosition.y)
                                    if(Math.pow(delta.x*delta.x + delta.y*delta.y, 0.5) > 5 && modelObj.ready) {
                                        modelObj.drag()
                                    }
                                }
                            }

                            SContextMenu {
                                y: 35
                                id: contextMenu
                                width: 120
                                SContextMenuItem {
                                    text: root.tr("Clear", "General")
                                    onPressed: {
                                        MERGER.deleteOutput(sql_id)
                                    }
                                }
                                SContextMenuItem {
                                    text: root.tr("Clear to right", "General")
                                    onPressed: {
                                        MERGER.deleteOutputAfter(sql_id)
                                    }
                                }

                                SContextMenuSeparator { }

                                SContextMenuItem {
                                    text: root.tr("Save", "General")
                                    onTriggered: {
                                        saveDialog.open()
                                    }
                                }

                                SContextMenuSeparator { }

                                SContextMenuItem {
                                    text: root.tr("Open", "General")
                                    onTriggered: {
                                        GALLERY.doOpenFiles([modelObj.file])
                                    }
                                }

                                SContextMenuItem {
                                    text: root.tr("Visit", "General")
                                    onTriggered: {
                                        GALLERY.doVisitFiles([modelObj.file])
                                    }
                                }

                                SContextMenuSeparator { }

                                Sql {
                                    id: destinationsSql
                                    query: "SELECT name, folder FROM folders WHERE UPPER(name) != UPPER('" + modelObj.mode + "');"
                                }

                                SContextMenu {
                                    id: copyToMenu
                                    title: root.tr("Copy to", "General")
                                    width: 120
                                    Instantiator {
                                        model: destinationsSql
                                        SContextMenuItem {
                                            text: sql_name
                                            onTriggered: {
                                                GALLERY.doCopy(sql_folder, [modelObj.file])
                                            }
                                        }
                                        onObjectAdded: copyToMenu.insertItem(index, object)
                                        onObjectRemoved: copyToMenu.removeItem(object)
                                    }
                                }
                            }

                            FileDialog {
                                id: saveDialog
                                title: root.tr("Save image", "General")
                                nameFilters: [root.tr("Image files") + " (*.png)"]
                                fileMode: FileDialog.SaveFile
                                defaultSuffix: "png"
                                onAccepted: {
                                    modelObj.saveImage(saveDialog.file)
                                }
                            }
                        }

                        Keys.onPressed: {
                            event.accepted = true
                            if(event.modifiers & Qt.ControlModifier) {
                                switch(event.key) {
                                case Qt.Key_C:
                                    modelObj.copy()
                                    break;
                                default:
                                    event.accepted = false
                                    break;
                                }
                            } else {
                                switch(event.key) {
                                case Qt.Key_Left:
                                    MERGER.left()
                                    break
                                case Qt.Key_Right:
                                    MERGER.right()
                                    break 
                                case Qt.Key_Delete:
                                    MERGER.deleteOutput(sql_id)
                                    break;
                                default:
                                    event.accepted = false
                                    break;
                                }
                            }
                        }
                    }
                }

                header: Item {
                    height: parent.height
                    width: 9
                }

            }
        }

        SDividerHB {
            id: resultDivider
            minOffset: snap
            maxOffset: parent.height-snap
            offset: snap
            snap: 150
            snapSize: 20
            height: 4
            color: "transparent"
            Rectangle {
                anchors.fill: parent
                color: COMMON.bg5
                anchors.topMargin: 1
                anchors.bottomMargin: 1
            }
        }
    }

    SDividerVL {
        id: divider
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        offset: parent.width / 2
        snap: parent.width / 2
        minOffset: 0
        maxOffset: parent.width - 5
        overflow: 8
    }

    Keys.onPressed: {
        event.accepted = true
        switch(event.key) {
        case Qt.Key_Delete:
            MERGER.deleteOperation()
            break;
        default:
            event.accepted = false
            break;
        }
    }
}