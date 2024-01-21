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

    function tr(str, file = "Trainer.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    SShadow {
        color: COMMON.bg0
        anchors.fill: parent
    }

    Flickable {
        id: flickable
        anchors.fill: parent
        contentHeight: container.height
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        interactive: false

        ScrollBar.vertical: SScrollBarV {
            id: scrollBar
            totalLength: flickable.contentHeight
            showLength: flickable.height
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: {
                scrollBar.doIncrement(wheel.angleDelta.y)
            }
        }

        Item {
            id: container
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 10
            width: Math.min(900, parent.width - 200)
            height: Math.max(optionsColumn.y + optionsColumn.height, statusBox.y + statusBox.height) + 20

            Rectangle {
                id: buttonBox
                anchors.horizontalCenter: optionsColumn.horizontalCenter
                anchors.top: parent.top
                height: 32
                width: 180
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2

                Row {
                    anchors.fill: parent
                    anchors.margins: 3

                    SButton {
                        label: "Save"
                        width: parent.width/3
                        height: parent.height
                        onPressed: {
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

                    SButton {
                        label: "Reset"
                        width: parent.width/3
                        height: parent.height
                        onPressed: {
                            TRAINER.reset()
                        }
                    }

                    FileDialog {
                        id: loadFileDialog
                        nameFilters: [root.tr("Config files") + " (*.json)"]

                        onAccepted: {
                            TRAINER.loadConfig(file)
                        }
                    }

                    FileDialog {
                        id: saveFileDialog
                        nameFilters: [root.tr("Config files") + " (*.json)"]
                        fileMode: FileDialog.SaveFile
                        defaultSuffix: "json"
                        onAccepted: {
                            TRAINER.saveConfig(file)
                        }
                    }
                }
            }

            Column {
                id: optionsColumn
                width: 200
                anchors.left: parent.left
                anchors.top: buttonBox.bottom
                anchors.topMargin: -2
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
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OChoice {
                        id: typeChoice
                        height: 30
                        width: parent.width
                        label: "Type"

                        bindMap: TRAINER.parameters
                        bindKeyCurrent: "type"
                        bindKeyModel: "types"
                    }

                    OTextInput {
                        height: 30
                        width: parent.width
                        label: "Name"

                        bindMap: TRAINER.parameters
                        bindKey: "name"
                        placeholder: root.tr("...", "Options")
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
                        text: "Network"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OSlider {
                        label: "Rank"
                        width: parent.width
                        height: 30

                        minValue: 8
                        maxValue: 256
                        precValue: 0
                        incValue: 8
                        snapValue: 8

                        bindMap: TRAINER.parameters
                        bindKey: "lora_rank"
                    }

                    OSlider {
                        label: "Alpha"
                        width: parent.width
                        height: 30

                        minValue: 1
                        maxValue: 256
                        precValue: 0
                        incValue: 1
                        snapValue: 8

                        bindMap: TRAINER.parameters
                        bindKey: "lora_alpha"
                    }

                    OSlider {
                        visible: typeChoice.value == "LoCon"
                        label: "Conv Rank"
                        width: parent.width
                        height: visible ? 30 : 0

                        minValue: 8
                        maxValue: 256
                        precValue: 0
                        incValue: 8
                        snapValue: 8

                        bindMap: TRAINER.parameters
                        bindKey: "lora_conv_rank"
                    }

                    OSlider {
                        visible: typeChoice.value == "LoCon"
                        label: "Conv Alpha"
                        width: parent.width
                        height: visible ? 30 : 0

                        minValue: 1
                        maxValue: 256
                        precValue: 0
                        incValue: 1
                        snapValue: 8

                        bindMap: TRAINER.parameters
                        bindKey: "lora_conv_alpha"
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
                        text: "Model"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OChoice {
                        id: modeChoice
                        height: 30
                        width: parent.width
                        label: "Base"

                        bindMapCurrent: TRAINER.parameters
                        bindKeyCurrent: "base_model"
                        bindMapModel: BASIC.parameters.values
                        bindKeyModel: "models"

                        function display(text) {
                            return GUI.modelName(text)
                        }
                    }

                    OSlider {
                        label: "CLIP Skip"
                        width: parent.width
                        height: 30

                        minValue: 1
                        maxValue: 4
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: true

                        bindMap: TRAINER.parameters
                        bindKey: "clip_skip"
                    }

                    OChoice {
                        label: "Prediction"
                        width: parent.width
                        height: 30

                        bindMap: TRAINER.parameters
                        bindKeyCurrent: "prediction_type"
                        bindKeyModel: "prediction_types"
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
                        text: "Learning"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OSlider {
                        label: "Steps"
                        width: parent.width
                        height: 30

                        value: 5000
                        minValue: 1000
                        maxValue: 10000
                        precValue: 0
                        incValue: 1000
                        snapValue: 1000
                        bounded: false

                        bindMap: TRAINER.parameters
                        bindKey: "steps"
                    }

                    OSlider {
                        label: "Rate"
                        width: parent.width
                        height: 30

                        value: 0.0001
                        minValue: 0.00001
                        maxValue: 0.0005
                        precValue: 5
                        incValue: 0.00001
                        snapValue: 0.00005
                        bounded: false

                        bindMap: TRAINER.parameters
                        bindKey: "learning_rate"
                    }

                    OChoice {
                        id: scheduleChoice
                        label: "Schedule"
                        width: parent.width
                        height: 30

                        bindMap: TRAINER.parameters
                        bindKeyCurrent: "learning_schedule"
                        bindKeyModel: "learning_schedules"
                    }

                    OSlider {
                        label: "Warmup"
                        width: parent.width
                        height: 30

                        minValue: 0
                        maxValue: 1
                        precValue: 2
                        incValue: 0.01
                        snapValue: 0.05

                        bindMap: TRAINER.parameters
                        bindKey: "warmup"
                    }

                    OSlider {
                        visible: scheduleChoice.value == "Cosine"
                        label: "Restarts"
                        width: parent.width
                        height: visible ? 30 : 0

                        minValue: 1
                        maxValue: 8
                        precValue: 0
                        incValue: 1
                        snapValue: 1
                        bounded: false

                        bindMap: TRAINER.parameters
                        bindKey: "restarts"
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
                        text: "Bucketing"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OSlider {
                        label: "Image Size"
                        width: parent.width
                        height: 30

                        minValue: 512
                        maxValue: 1024
                        precValue: 0
                        incValue: 64
                        snapValue: 128
                        bounded: false

                        bindMap: TRAINER.parameters
                        bindKey: "image_size"
                    }

                    OSlider {
                        label: "Batch Size"
                        width: parent.width
                        height: 30

                        minValue: 1
                        maxValue: 16
                        precValue: 0
                        incValue: 2
                        snapValue: 2
                        bounded: false

                        bindMap: TRAINER.parameters
                        bindKey: "batch_size"
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
                        text: "Caption"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        topPadding: 1
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Column {
                    x: 10
                    width: parent.width - 20

                    OChoice {
                        label: "Shuffle"
                        width: parent.width
                        height: 30

                        bindMap: TRAINER.parameters
                        bindKeyCurrent: "shuffle"
                        bindKeyModel: "enabled_disabled"
                    }
                }

                Item {
                    width: parent.width
                    height: 4
                }
            }

            Rectangle {
                anchors.fill: optionsColumn
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }

            Rectangle {
                anchors.fill: foldersColumn
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }

            Column {
                id: foldersColumn
                anchors.left: optionsColumn.right
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.leftMargin: 10

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
                        text: "Folders"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }

                    SIconButton {
                        visible: TRAINER.currentFolder != ""
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 1
                        anchors.topMargin: 2
                        anchors.rightMargin: 5
                        color: "transparent"
                        height: 23
                        width: 23
                        tooltip: root.tr("Add folder")
                        icon: "qrc:/icons/folder.svg"
                        onPressed: {
                            addFolderDialog.open()
                        }
                    }

                    FolderDialog {
                        id: addFolderDialog

                        onAccepted: {
                            TRAINER.addFolder(folder)
                        }
                    }
                }

                Item {
                    width: parent.width
                    height: 2

                    Rectangle {
                        id: sideBar
                        color: COMMON.bg6
                        x: parent.width + 2
                        y: 0
                        width: 6
                        height: datasetList.height - y + 35
                        visible: TRAINER.currentFolder != ""
                    }

                    Rectangle {
                        anchors.bottom: sideBar.bottom
                        anchors.right: sideBar.left
                        color: COMMON.bg6
                        height: 6
                        width: 6
                        visible: sideBar.visible
                    }
                }

                ListView {
                    id: datasetList
                    model: TRAINER.folders
                    x: 10
                    width: parent.width - 20
                    height: TRAINER.currentFolder == "" ? 25 : contentHeight

                    SIconButton {
                        visible: TRAINER.currentFolder == ""
                        anchors.centerIn: parent
                        color: "transparent"
                        height: 23
                        width: 23
                        inset: 5
                        tooltip: root.tr("Add folder")
                        icon: "qrc:/icons/folder.svg"
                        onPressed: {
                            addFolderDialog.open()
                        }
                    }
                    
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: SScrollBarV {
                        totalLength: datasetList.contentHeight
                        showLength: datasetList.height
                    }

                    delegate: Rectangle {
                        height: 25
                        width: parent.width
                        color: selected ? COMMON.bg2 : COMMON.bg0

                        property var selected: TRAINER.currentFolder == modelData

                        Rectangle {
                            visible: selected
                            color: COMMON.bg6
                            width: 12
                            height: 6
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.right

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
                                TRAINER.currentFolder = modelData
                                if (mouse.button & Qt.RightButton) {
                                    datasetContextMenu.popup()
                                }
                            }
                        }

                        SContextMenu {
                            id: datasetContextMenu
                            SContextMenuItem {
                                height: 20
                                text: root.tr("Delete")
                                onPressed: {
                                    TRAINER.deleteFolder()
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
                                    pointSize: 9.8
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
                                width: parent.width - 100
                                color: selected ? COMMON.bg3 : COMMON.bg0

                                OText {
                                    id: folderText
                                    width: parent.width
                                    height: parent.height
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                    pointSize: 9.4
                                    color: COMMON.fg1

                                    text: modelData
                                }
                            }

                            Rectangle {
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            OText {
                                width: parent.width - x
                                height: parent.height
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                pointSize: 9.4
                                color: COMMON.fg1_5
                                elide: Text.ElideRight
                                leftPadding: 3
                                rightPadding: 3
                                text: TRAINER.images(modelData).length
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
                id: datasetBox
                anchors.left: foldersColumn.left
                anchors.right: foldersColumn.right
                anchors.top: foldersColumn.bottom
                anchors.topMargin: 10
                height: 409

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
                        text: "Dataset"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Item {
                    anchors.fill: parent
                    anchors.margins: 2
                    anchors.topMargin: 30

                    Rectangle {
                        id: imageListBox
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        width: 200
                        anchors.margins: 2
                        color: "transparent"
                        border.color: COMMON.bg4

                        Image {
                            id: placeholderList
                            visible: imageList.model.length == 0
                            source: "qrc:/icons/placeholder_black.svg"
                            height: 30
                            width: height
                            sourceSize: Qt.size(width*1.25, height*1.25)
                            anchors.centerIn: parent
                        }

                        ColorOverlay {
                            visible: placeholderList.visible
                            anchors.fill: placeholderList
                            source: placeholderList
                            color: COMMON.bg3
                        }

                        ListView {
                            id: imageList
                            anchors.fill: parent
                            anchors.margins: 1

                            clip: true
                            interactive: false
                            boundsBehavior: Flickable.StopAtBounds

                            ScrollBar.vertical: SScrollBarV {
                                id: imageScrollBar

                                totalLength: imageList.contentHeight
                                showLength: imageList.height
                                incrementLength: 60
                            }

                            Rectangle {
                                visible: imageScrollBar.showing
                                x: parent.width - 11
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }

                            Rectangle {
                                visible: !imageScrollBar.showing && imageList.model.length != 0
                                width: parent.width
                                height: 1
                                y: parent.contentHeight
                                color: COMMON.bg4
                            }

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.NoButton
                                onWheel: {
                                    imageScrollBar.doIncrement(imageScrollBar)
                                }
                            }

                            Connections {
                                target: TRAINER
                                function onCurrentImageChanged() {
                                    var index = imageList.model.indexOf(TRAINER.currentImage)
                                    imageList.positionViewAtIndex(index, ListView.Contain)
                                    imageList.currentIndex = index
                                }
                            }

                            model: TRAINER.currentImages

                            delegate: Rectangle {
                                id: row
                                color: index % 2 == 0 ? COMMON.bg1 : COMMON.bg0
                                width: imageList.width - (imageScrollBar.showing ? 10 : 0)
                                height: 16

                                property var selected: TRAINER.currentImage == modelData

                                Rectangle {
                                    x: 40
                                    height: parent.height
                                    width: 1
                                    color: COMMON.bg3
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    opacity: parent.selected ? 0.1 : 0.0
                                }

                                Item {
                                    height: parent.height
                                    width: 40
                                    SText {
                                        anchors.fill: parent
                                        text: index
                                        color: row.selected ? COMMON.fg1_5 : COMMON.fg2
                                        monospace: true
                                        pointSize: 9.5
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignHCenter
                                        opacity: 0.75
                                    }
                                }

                                Item {
                                    x: 40
                                    height: parent.height
                                    width: parent.width - 40
                                    SText {
                                        anchors.fill: parent
                                        text: GUI.modelFileName(modelData)
                                        color: row.selected ? COMMON.fg1 : COMMON.fg2
                                        monospace: true
                                        leftPadding: 5
                                        rightPadding: 3
                                        bottomPadding: 2
                                        elide: Text.ElideRight
                                        pointSize: 9.5
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignLeft
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onPressed: {
                                        TRAINER.currentImage = modelData
                                        imageList.forceActiveFocus()
                                    }
                                }
                            }
                            Keys.onPressed: {
                                event.accepted = true
                                switch(event.key) {
                                case Qt.Key_Up:
                                    var index = imageList.model.indexOf(TRAINER.currentImage) - 1
                                    if (index >= 0) {
                                        TRAINER.currentImage = imageList.model[index]
                                    }
                                    break;
                                case Qt.Key_Down:
                                    var index = imageList.model.indexOf(TRAINER.currentImage) + 1
                                    if (index < imageList.model.length) {
                                        TRAINER.currentImage = imageList.model[index]
                                    }
                                    break;
                                default:
                                    event.accepted = false
                                    break;
                                }
                            }
                        }

                        
                    }

                    Rectangle {
                        id: imageListDivider
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.left: imageListBox.right
                        anchors.leftMargin: 2
                        width: 2
                        color: COMMON.bg4
                    }

                    Rectangle {
                        id: imagePromptDivider
                        anchors.left: imageListDivider.right
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 100
                        height: 2
                        color: COMMON.bg4
                    }

                    Rectangle {
                        id: promptBox
                        anchors.top: imagePromptDivider.bottom
                        anchors.bottom: parent.bottom
                        anchors.left: imageListDivider.right
                        anchors.right: parent.right
                        anchors.margins: 2
                        color: COMMON.bg1
                        border.color: COMMON.bg4

                        STextArea {
                            id: prompt
                            anchors.fill: parent
                            anchors.margins: 1
                            pointSize: 9.8
                            readOnly: TRAINER.currentImage == ""

                            Connections {
                                target: TRAINER
                                function onCurrentPromptChanged() {
                                    prompt.text = TRAINER.currentPrompt
                                }
                            }

                            Rectangle {
                                visible: prompt.scrollBar.showing
                                x: parent.width - 11
                                width: 1
                                height: parent.height
                                color: COMMON.bg4
                            }
                        }
                    }

                    Item {
                        id: imageBox
                        anchors.top: parent.top
                        anchors.left: imageListDivider.right
                        anchors.right: parent.right
                        anchors.bottom: imagePromptDivider.top

                        SShadow {
                            anchors.fill: parent
                        }

                        Image {
                            id: placeholderImage
                            visible: view.sourceWidth == 0
                            source: "qrc:/icons/placeholder_black.svg"
                            height: 50
                            width: height
                            sourceSize: Qt.size(width*1.25, height*1.25)
                            anchors.centerIn: parent
                        }

                        ColorOverlay {
                            visible: placeholderImage.visible
                            anchors.fill: placeholderImage
                            source: placeholderImage
                            color: COMMON.bg3
                        }

                        MovableImage {
                            //visible: false
                            id: view
                            anchors.fill: parent

                            source: TRAINER.currentImage
                            sourceWidth: TRAINER.currentImageWidth
                            sourceHeight: TRAINER.currentImageHeight
                        }

                        Item {
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.left: sizeInfoText.left
                            height: 20
                            clip: true

                            Rectangle {
                                id: sizeInfo
                                anchors.top: parent.top
                                anchors.topMargin: -5
                                width: parent.width
                                height: 25
                                opacity: 0.8
                                visible: sizeInfoText.visible
                                color: "#c0101010"
                                border.width: 1
                                border.color: COMMON.bg3
                            }
                        }

                        SText {
                            id: sizeInfoText
                            visible: text != ""
                            anchors.top: parent.top
                            anchors.right: parent.right
                            verticalAlignment: Text.AlignVCenter
                            rightPadding: 8
                            leftPadding: 8
                            topPadding: 1
                            bottomPadding: 8
                            pointSize: 9
                            color: COMMON.fg1_5
                            text: view.sourceWidth != 0 ? view.sourceWidth + "x" + view.sourceHeight : ""
                        }
                    }
                }
            }

            Rectangle {
                anchors.fill: datasetBox
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }

            Item {
                id: statusBox
                anchors.left: foldersColumn.left
                anchors.right: foldersColumn.right
                anchors.top: datasetBox.bottom
                anchors.topMargin: 10
                height: 200

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
                        text: "Training"
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        bottomPadding: 2
                        font.weight: Font.Medium
                        pointSize: 10.5
                        color: COMMON.fg1
                    }
                }

                Item {
                    anchors.fill: parent
                    anchors.topMargin: 30

                    Rectangle {
                        id: rateChart
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.bottom: parent.bottom
                        anchors.margins: 10
                        width: height
                        color: "transparent"
                        border.width: 1
                        border.color: COMMON.bg4

                        SText {
                            text: "Rate"
                            anchors.top: parent.top
                            anchors.left: parent.left
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            leftPadding: 5
                            
                        }

                        SText {
                            text: TRAINER.learningRateCurrentValue
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            font.bold: true
                            monospace: true
                            leftPadding: 5
                        }

                        SText {
                            text: TRAINER.learningRateMax
                            anchors.top: parent.top
                            anchors.right: parent.right
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            rightPadding: 5
                        }

                        SText {
                            text: TRAINER.learningRateMin
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            rightPadding: 5
                        }

                        Rectangle {
                            id: lrArea
                            anchors.fill: parent
                            anchors.topMargin: 20
                            anchors.bottomMargin: 20
                            color: COMMON.bg0
                            border.width: 1
                            border.color: COMMON.bg4
                            clip: true

                            property var currentX: TRAINER.learningRateCurrentPoint.x * width
                            property var currentY: (1-TRAINER.learningRateCurrentPoint.y) * (height-2)
                            property var progressX: TRAINER.trainingProgress * width

                            Rectangle {
                                id: lrCompleted
                                visible: parent.progressX != 0
                                x: 0
                                y: 0
                                width: parent.progressX
                                height: parent.height - 1
                                color: COMMON.bg1
                            }

                            Rectangle {
                                anchors.left: lrCompleted.right
                                visible: lrCompleted.visible
                                width: 1
                                height: parent.height - 1
                                color: COMMON.bg3
                            }
                            
                            Repeater {
                                model: 4
                                Rectangle {
                                    x: (index/4) * parent.width
                                    y: 0
                                    width: 1
                                    height: parent.height
                                    color: COMMON.bg4
                                }
                            }
                            Repeater {
                                model: 4
                                Rectangle {
                                    x: 0
                                    y: (index/4) * parent.height
                                    width: parent.width
                                    height: 1
                                    color: COMMON.bg4
                                }
                            }
                        
                            Canvas {
                                renderStrategy: Canvas.Cooperative
                                property var points: TRAINER.learningRatePoints

                                onPointsChanged: {
                                    requestPaint()
                                }

                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.clearRect(0, 0, width, height);

                                    ctx.strokeStyle = COMMON.fg0;
                                    ctx.lineWidth = 1.5;
                                    ctx.beginPath();
                                    for(var i = 0; i < points.length; i++) {
                                        var p = points[i]
                                        var x = p.x * width
                                        var y = (height-2) - p.y * (height-2) + 1
                                        if (i == 0) {
                                            ctx.moveTo(x, y)
                                        }
                                        ctx.lineTo(x, y)
                                    }
                                    ctx.stroke()
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true

                                onPositionChanged: {
                                    TRAINER.setLearningRateCurrent(mouse.x/parent.width)
                                }

                                onExited: {
                                    TRAINER.setLearningRateCurrent(-1)
                                }
                            }

                            Rectangle {
                                id: lrCurrentX
                                visible: TRAINER.learningRateCurrentPoint.x != 0
                                x: parent.currentX - 1
                                y: 0
                                width: 2
                                height: parent.height
                                opacity: 0.8
                                color: COMMON.accent(0)
                            }

                            Rectangle {
                                id: lrCurrentY
                                visible: TRAINER.learningRateCurrentPoint.y != 0
                                x: 0
                                y: parent.currentY - 1
                                width: parent.width
                                height: 2
                                opacity: 0.8
                                color: COMMON.accent(0)
                            }

                            Rectangle {
                                visible: TRAINER.learningRateCurrentPoint.y != 0
                                width: 6
                                height: 6
                                radius: 3
                                opacity: 0.8
                                color: "red"
                                x: lrCurrentX.x - 2
                                y: lrCurrentY.y - 2
                            }
                        }
                    }

                    Rectangle {
                        id: lossChart
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 10
                        width: height
                        color: "transparent"
                        border.width: 1
                        border.color: COMMON.bg4

                        SText {
                            text: "Loss"
                            anchors.top: parent.top
                            anchors.left: parent.left
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            leftPadding: 5
                        }

                        SText {
                            text: TRAINER.lossCurrentValue
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            font.bold: true
                            monospace: true
                            leftPadding: 5
                        }

                        SText {
                            text: TRAINER.lossMax
                            anchors.top: parent.top
                            anchors.right: parent.right
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            rightPadding: 5
                        }

                        SText {
                            text: TRAINER.lossMin
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            height: 20
                            verticalAlignment: Text.AlignVCenter
                            font.pointSize: 8
                            font.letterSpacing: -0.5
                            color: COMMON.fg3
                            monospace: true
                            rightPadding: 5
                        }

                        Rectangle {
                            id: lossArea
                            anchors.fill: parent
                            anchors.topMargin: 20
                            anchors.bottomMargin: 20
                            color: COMMON.bg0
                            border.width: 1
                            border.color: COMMON.bg4
                            clip: true
                            
                            property var currentX: TRAINER.lossCurrentPoint.x * width
                            property var currentY: (1-TRAINER.lossCurrentPoint.y) * (height-2)
                            property var pinned: Math.abs(currentX - width) < 1

                            Repeater {
                                model: 4
                                Rectangle {
                                    x: (index/4) * parent.width
                                    y: 0
                                    width: 1
                                    height: parent.height
                                    color: COMMON.bg4
                                }
                            }
                            Repeater {
                                model: 4
                                Rectangle {
                                    x: 0
                                    y: (index/4) * parent.height
                                    width: parent.width
                                    height: 1
                                    color: COMMON.bg4
                                }
                            }

                            Canvas {
                                renderStrategy: Canvas.Cooperative
                                property var points: TRAINER.lossPoints

                                onPointsChanged: {
                                    requestPaint()
                                }

                                anchors.fill: parent
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.clearRect(0, 0, width, height);

                                    ctx.strokeStyle = COMMON.fg0;
                                    ctx.lineWidth = 1.5;
                                    ctx.beginPath();
                                    for(var i = 0; i < points.length; i++) {
                                        var p = points[i]
                                        var x = p.x * width
                                        var y = (height-2) - p.y * (height-2) + 1
                                        if (i == 0) {
                                            ctx.moveTo(x, y)
                                        }
                                        ctx.lineTo(x, y)
                                    }
                                    ctx.stroke()
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true

                                onPositionChanged: {
                                    TRAINER.setLossCurrent(mouse.x/parent.width)
                                }

                                onExited: {
                                    TRAINER.setLossCurrent(-1)
                                }
                            }

                            Rectangle {
                                id: lossCurrentX
                                visible: parent.currentX != 0 && !parent.pinned
                                x: parent.currentX - 1
                                y: 0
                                width: 2
                                height: parent.height
                                opacity: 0.8
                                color: COMMON.accent(0)
                            }

                            Rectangle {
                                id: lossCurrentY
                                visible: TRAINER.lossCurrentPoint.y != 0
                                x: 0
                                y: parent.currentY - 1
                                width: parent.width
                                height: 2
                                opacity: 0.8
                                color: COMMON.accent(0)
                            }

                            Rectangle {
                                visible: TRAINER.lossCurrentPoint.y != 0
                                width: 6
                                height: 6
                                radius: 3
                                opacity: 0.8
                                color: "red"
                                x: lossCurrentX.x - 2
                                y: lossCurrentY.y - 2
                            }
                        }
                    }

                    Column {
                        anchors.left: rateChart.right
                        anchors.right: lossChart.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.margins: 8

                        SButton {
                            visible: TRAINER.stageLabel == "Idle"
                            width: parent.width
                            height: visible ? 25 : 0

                            label: "Start"

                            onPressed: {
                                TRAINER.train()
                            }
                        }

                        Row {
                            visible: TRAINER.stageLabel != "Idle"
                            width: parent.width
                            height: visible ? 25 : 0
                            spacing: 0
                            property var elementWidth: (width-(spacing*1))/2
                            SButton {
                                width: parent.elementWidth
                                height: 25

                                label: "Stop"

                                onPressed: {
                                    TRAINER.stop()
                                }
                            }
                            SButton {
                                width: parent.elementWidth
                                height: 25

                                label: "Pause"

                                onPressed: {
                                    
                                }
                            }
                        }
                        
                        Item {
                            width: parent.width
                            height: 30

                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 2
                                color: "transparent"
                                border.color: COMMON.bg4
                                border.width: 1

                                Item {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    clip: true

                                    property var active: TRAINER.epochMarks.length != 0
                                    property var currentProgress: Math.floor(TRAINER.progress * width)
                                    property var currentLR: Math.floor(TRAINER.learningRateCurrentPoint.x * width)
                                    property var currentLoss: Math.floor(TRAINER.lossCurrentPoint.x * TRAINER.trainingProgress * width)

                                    Rectangle {
                                        id: progressBar
                                        visible: TRAINER.progress != 0
                                        width: parent.currentProgress
                                        height: parent.height
                                        color: COMMON.bg1_5
                                    }

                                    Rectangle {
                                        id: current
                                        visible: TRAINER.progress != 0
                                        x: parent.currentProgress
                                        height: parent.height
                                        width: 1
                                        color: COMMON.bg3
                                    }

                                    Repeater {
                                        model: TRAINER.epochMarks

                                        Item {
                                            x: (parent.width * modelData) - 1
                                            y: 0
                                            height: parent.height
                                            width: 1

                                            visible: false

                                            Timer {
                                                interval: (index/TRAINER.epochMarks.length) * 1000
                                                running: true
                                                onTriggered: {
                                                    parent.visible = true
                                                }
                                            }
                                            
                                            Rectangle {
                                                color: COMMON.bg4
                                                width: 1
                                                height: 4
                                            }

                                            Rectangle {
                                                color: COMMON.bg4
                                                y: parent.height - height
                                                width: 1
                                                height: 4
                                            }
                                        }
                                    }

                                    Rectangle {
                                        id: marker
                                        visible: parent.active && Math.abs(parent.currentLR - parent.currentLoss) < 2
                                        x: parent.currentLR
                                        height: parent.height
                                        width: 1
                                        color: "red"
                                    }

                                    Rectangle {
                                        id: lrMarker
                                        visible: parent.active && !marker.visible
                                        x: parent.currentLR
                                        height: parent.height
                                        width: 1
                                        opacity: 0.5
                                        color: "red"
                                    }

                                    Rectangle {
                                        id: lossMarker
                                        visible: parent.active && !marker.visible
                                        x: parent.currentLoss
                                        height: parent.height
                                        width: 1
                                        opacity: 0.5
                                        color: "red"
                                    }

                                    MouseArea {
                                        visible: parent.active
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onPositionChanged: {
                                            if(mouseX < parent.currentProgress) {
                                                TRAINER.setLossCurrent(mouse.x/parent.currentProgress)
                                            } else {
                                                TRAINER.setLossCurrent(-1)
                                            }
                                            TRAINER.setLearningRateCurrent(mouse.x/parent.width)
                                        }

                                        onExited: {
                                            TRAINER.setLearningRateCurrent(-1)
                                            TRAINER.setLossCurrent(-1)
                                        }
                                    }
                                }
                            }
                        }

                        Item {
                            width: parent.width
                            height: 24

                            Row {
                                anchors.fill: parent
                                anchors.margins: 2
                                spacing: 4
                                property var elementWidth: (width-(spacing*2))/3
                                Rectangle {
                                    width: parent.elementWidth
                                    height: parent.height
                                    color: "transparent"
                                    border.color: COMMON.bg4
                                    border.width: 1

                                    SText {
                                        anchors.fill: parent
                                        text: TRAINER.progressLabel
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pointSize: 9
                                        font.letterSpacing: -0.5
                                        color: COMMON.fg3
                                        monospace: true
                                    }
                                }
                                Rectangle {
                                    width: parent.elementWidth
                                    height: parent.height
                                    color: "transparent"
                                    border.color: COMMON.bg4
                                    border.width: 1

                                    SText {
                                        anchors.fill: parent
                                        text: TRAINER.stageLabel
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pointSize: 9
                                        font.letterSpacing: -0.5
                                        color: COMMON.fg3
                                        monospace: true
                                    }
                                }
                                Rectangle {
                                    width: parent.elementWidth
                                    height: parent.height
                                    color: "transparent"
                                    border.color: COMMON.bg4
                                    border.width: 1

                                    SText {
                                        anchors.fill: parent
                                        text: TRAINER.remainingLabel
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pointSize: 9
                                        font.letterSpacing: -0.5
                                        color: COMMON.fg3
                                        monospace: true
                                    }
                                }
                            }
                        }

                        Item {
                            width: parent.width
                            height: 60

                            SText {
                                anchors.fill: parent
                                text: "WORK IN PROGRESS"
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.pointSize: 9
                                font.letterSpacing: -0.5
                                color: COMMON.bg4
                                monospace: true
                            }
                        }
                    }
                }
            }

            Rectangle {
                anchors.fill: statusBox
                color: "transparent"
                border.color: COMMON.bg4
                border.width: 2
            }
        }
    }
}