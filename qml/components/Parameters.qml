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


            progress: GUI.statusProgress
            working: GUI.statusMode == 2
            disabled: GUI.statusMode != 1
            info: GUI.statusInfo

            onPressed: {
                root.generate()
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
                    }
                    OSlider {
                        id: stepsInput
                        label: "Steps"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "steps"

                        minValue: 1
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
                        tooltip: "Sampler"
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

                    property var componentMode: false

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

                        disabled: modelColumn.componentMode

                        onTryEnter: {
                            modelColumn.componentMode = false
                        }
                    }

                    OChoice {
                        id: unetInput
                        label: "UNET"
                        width: parent.width
                        height: 25
                        
                        bindMap: root.binding.values
                        bindKeyCurrent: "UNET"
                        bindKeyModel: "UNETs"

                        disabled: !modelColumn.componentMode
                        onTryEnter: {
                            modelColumn.componentMode = true
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
                        
                        disabled: !modelColumn.componentMode
                        onTryEnter: {
                            modelColumn.componentMode = true
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

                        disabled: !modelColumn.componentMode
                        onTryEnter: {
                            modelColumn.componentMode = true
                        }
                    }
                }

                OColumn {
                    id: netColumn
                    text: "Networks"
                    width: parent.width
                    padding: false

                    onExpanded: {
                        paramScroll.position(netColumn)
                    }

                    Item {
                        width: parent.width
                        height: Math.max(100, paramScroll.height-(netColumn.y+33))

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

                                    ParametersNetSlider {
                                        anchors.fill: parent
                                        anchors.rightMargin: scrollBar.policy == ScrollBar.AlwaysOn ? 8 : 0
                                        label: modelData.name
                                        type:  modelData.type

                                        onDeactivate: {
                                            root.binding.deleteNetwork(index)
                                        }

                                        value: modelData.strength
                                        onValueChanged: {
                                            if(modelData.strength != value) {
                                                modelData.strength = value
                                                value = Qt.binding(function() {return modelData.strength;})
                                            }
                                        }

                                        minValue: 0
                                        maxValue: 2
                                        precValue: 2
                                        incValue: 0.01
                                        snapValue: 0.05
                                        bounded: false
                                    }
                                }
                            }
                        }
                    }
                }
                OColumn {
                    id: miscColumn
                    text: "Misc"
                    width: parent.width

                    onExpanded: {
                        paramScroll.position(miscColumn)
                    }

                    OSlider {
                        label: "CLIP Skip"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKey: "clip_skip"

                        minValue: 0
                        maxValue: 4
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
                        maxValue: 32
                        precValue: 0
                        incValue: 1
                        snapValue: 2
                        bounded: false
                    }
                    OChoice {
                        label: "Upscaler"
                        width: parent.width
                        height: 30

                        bindMap: root.binding.values
                        bindKeyCurrent: "img2img_upscaler"
                        bindKeyModel: "img2img_upscalers"
                    }
                    OSlider {
                        label: "HR Factor"
                        width: parent.width
                        height: 30

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

                        bindMap: root.binding.values
                        bindKeyCurrent: "hr_upscaler"
                        bindKeyModel: "hr_upscalers"
                    }
                }
            }
        }
    }
}