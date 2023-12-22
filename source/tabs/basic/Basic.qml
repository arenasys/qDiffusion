import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 1.0


import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    clip: true
    property var swap: false
    property var autocomplete: false

    function syncSwap() {
        var swp = GUI.config.get("swap")
        var aut = GUI.config.get("autocomplete")

        if(swp != root.swap) {
            root.swap = swp
        }

        if(aut != root.autocomplete) {
            root.autocomplete = aut
        }
    }

    Connections {
        target: GUI.config
        function onUpdated() {
            syncSwap()
        }
    }

    Component.onCompleted: {
        syncSwap()
    }
    
    onSwapChanged: {
        leftDivider.offset = 210
        rightDivider.offset = 210
    }

    function tr(str, file = "Basic.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    function releaseFocus() {
        parent.releaseFocus()
    }

    SDialog {
        id: buildDialog
        title: root.tr("Build model")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        dim: true

        Connections {
            target: BASIC
            function onStartBuildModel() {
                buildDialog.open()
            }
        }

        OTextInput {
            id: filenameInput
            width: 290
            height: 30
            label: root.tr("Filename")
            value: GUI.modelName(BASIC.parameters.values.get("UNET")) + ".safetensors"
        }

        width: 300
        height: 87

        onAccepted: {
            BASIC.buildModel(filenameInput.value)
        }
    }

    AdvancedDropArea {
        id: basicDrop
        anchors.fill: parent

        onDropped: {
            BASIC.pasteDrop(mimeData)
        }
    }

    Item {
        id: leftArea
        anchors.left: parent.left
        anchors.right: divider.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }
    
    Item {
        id: rightArea
        anchors.left: divider.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }

    property var divider: root.swap ? leftDivider : rightDivider
    property var mainArea: root.swap ? rightArea : leftArea
    property var settingsArea: root.swap ? leftArea : rightArea

    BasicAreas {
        id: areas
        clip: true
        anchors.left: mainArea.left
        anchors.top: mainArea.top
        anchors.right: mainArea.right
        anchors.bottom: promptDivider.top
    }

    BasicFull {
        id: full
        anchors.fill: areas

        onContextMenu: {
            if(BASIC.openedArea == "output" && full.target.ready) {
                fullContextMenu.popup()
            }
        }

        SContextMenu {
            id: fullContextMenu

            SContextMenuItem {
                text: root.tr("Show Parameters")
                checkable: true
                checked: fullParams.show
                onCheckedChanged: {
                    if(checked != fullParams.show) {
                        fullParams.show = checked
                        checked = Qt.binding(function() { return fullParams.show })
                    }
                }
            }

            property var output: full.target != null && full.target.file != ""

            SContextMenuSeparator {
                visible: fullContextMenu.output
            }

            SContextMenuItem {
                id: outputContext
                visible: fullContextMenu.output
                text: root.tr("Open", "General")
                onTriggered: {
                    GALLERY.doOpenFiles([full.file])
                }
            }

            SContextMenuItem {
                text: root.tr("Visit", "General")
                visible: fullContextMenu.output
                onTriggered: {
                    GALLERY.doVisitFiles([full.file])
                }
            }

            SContextMenuSeparator {
                visible: fullContextMenu.output
            }

            Sql {
                id: destinationsSql
                query: "SELECT name, folder FROM folders WHERE UPPER(name) != UPPER('" + full.file + "');"
            }

            SContextMenu {
                id: fullCopyToMenu
                title: root.tr("Copy to", "General")
                Instantiator {
                    model: destinationsSql
                    SContextMenuItem {
                        visible: fullContextMenu.output
                        text: sql_name
                        onTriggered: {
                            GALLERY.doCopy(sql_folder, [full.file])
                        }
                    }
                    onObjectAdded: fullCopyToMenu.insertItem(index, object)
                    onObjectRemoved: fullCopyToMenu.removeItem(object)
                }
            }
        }
    }

    Rectangle {
        id: settings
        color: COMMON.bg0
        anchors.left: settingsArea.left
        anchors.right: settingsArea.right
        anchors.top: settingsArea.top
        anchors.bottom: status.top

        Parameters {
            id: params
            anchors.fill: parent
            binding: BASIC.parameters
            swap: root.swap

            remaining: BASIC.manager.remaining

            onGenerate: {
                BASIC.generate()
            }
            onCancel: {
                BASIC.cancel()
            }
            onForeverChanged: {
                BASIC.forever = params.forever
            }
            onBuildModel: {
                BASIC.doBuildModel()
            }
            function sizeDrop(mimeData) {
                BASIC.sizeDrop(mimeData)
            }
            function seedDrop(mimeData) {
                BASIC.seedDrop(mimeData)
            }
        }
    }

    Status {
        id: status
        anchors.bottom: settingsArea.bottom
        anchors.left: settingsArea.left
        anchors.right: settingsArea.right
    }

    Prompts {
        id: prompts
        anchors.left: mainArea.left
        anchors.right: mainArea.right
        anchors.bottom: mainArea.bottom
        anchors.top: promptDivider.bottom
        
        positivePromptArea.menuActive: suggestions.visible
        negativePromptArea.menuActive: suggestions.visible

        bindMap: BASIC.parameters.values

        Component.onCompleted: {
            GUI.setHighlighting(positivePromptArea.area.textDocument)
            GUI.setHighlighting(negativePromptArea.area.textDocument)
        }

        onPositivePromptChanged: {
            BASIC.parameters.promptsChanged()
        }
        onNegativePromptChanged: {
            BASIC.parameters.promptsChanged()
        }
        onInspect: {
            BASIC.pasteText(positivePrompt)
        }
        onTab: {
            if(suggestions.visible) {
                suggestions.complete(suggestions.currentItem.text)
            } else {
                root.forceActiveFocus()
                prompts.inactive.forceActiveFocus()
            }
        }
        onMenu: {
            if(suggestions.visible) {
                if(dir == 0) {
                    promptCursor.typed = false
                } else {
                    suggestions.move(dir)
                }
            }
        }
    }

    Item {
        id: promptCursor
        visible: typed && prompts.cursorX != null && prompts.cursorText != ""
        x: visible ? prompts.x + prompts.cursorX : 0
        y: visible ? prompts.y + prompts.cursorY : 0
        width: 200
        height: prompts.cursorHeight

        property var typed: false
        property var targetStart: null
        property var targetEnd: null
        property var replace: false
        property var onlyModels: false

        function update() {
            BASIC.suggestions.updateSuggestions(prompts.cursorText, prompts.cursorPosition, onlyModels)
            promptCursor.targetStart = BASIC.suggestions.start(prompts.cursorText, prompts.cursorPosition)
            promptCursor.targetEnd = BASIC.suggestions.end(prompts.cursorText, prompts.cursorPosition)
        }

        function reset() {
            promptCursor.typed = false
        }

        Connections {
            target: prompts

            function onInput(key) {
                if(!root.autocomplete) {
                    return
                }
                if(key == Qt.Key_Control) {
                    promptCursor.onlyModels = true
                    promptCursor.update()
                }
                if(key == Qt.Key_Right || key == Qt.Key_Left) {
                    if (promptCursor.typed) {
                        promptCursor.update()
                    }
                } else if(key != Qt.Key_Down && key != Qt.Key_Right) {
                    if(!promptCursor.typed)  {
                        promptCursor.replace = BASIC.suggestions.replace(prompts.cursorText, prompts.cursorPosition)
                    }
                    promptCursor.typed = true
                }
            }

            function onRelease(key) {
                if(!root.autocomplete) {
                    return
                }
                if(key == Qt.Key_Control) {
                    promptCursor.onlyModels = false
                    promptCursor.update()
                }
            }

            function onCursorTextChanged() {
                if(!root.autocomplete) {
                    return
                }
                if(prompts.cursorText == null) {
                    promptCursor.reset()
                } else if (promptCursor.typed) {
                    promptCursor.update()
                }
            }
        }
    }

    Rectangle {
        visible: suggestions.visible
        anchors.fill: suggestions
        color: COMMON.bg2
        border.width: 1
        border.color: COMMON.bg4
        anchors.margins: -1
    }
    Rectangle {
        visible: suggestions.visible
        anchors.fill: suggestions
        color: "transparent"
        border.width: 1
        border.color: COMMON.bg0
        anchors.margins: -2
    }

    ListView {
        id: suggestions
        property var entries: BASIC.suggestions.results.length != 0
        visible: promptCursor.visible && entries
        property var flip: promptCursor.y + promptCursor.height + 60 > root.height
        anchors.left: promptCursor.left
        anchors.right: promptCursor.right
        anchors.bottom: flip ? promptCursor.top : undefined
        anchors.top: flip ? undefined : promptCursor.bottom
        anchors.topMargin: 3
        anchors.bottomMargin: 3
        height: Math.min(BASIC.suggestions.results.length, 3)*20
        clip: true
        model: BASIC.suggestions.results

        verticalLayoutDirection: flip ? ListView.BottomToTop : ListView.TopToBottom
        boundsBehavior: Flickable.StopAtBounds
        highlightFollowsCurrentItem: false

        onEntriesChanged: {
            if (!entries) {
                promptCursor.reset()
            }
        }

        function complete(text) {
            var curr = prompts.active
            curr.completeText(text, promptCursor.targetStart, promptCursor.replace ? promptCursor.targetEnd : prompts.cursorPosition)
        }

        function move(dir) {
            dir *= flip ? -1 : 1
            if(dir == 1) {
                decrementCurrentIndex()
            } else if (dir == -1) {
                incrementCurrentIndex()
            }
            positionViewAtIndex(currentIndex, ListView.Contain)
        }

        ScrollBar.vertical: SScrollBarV {
            id: suggestionsScrollBar
            padding: 0
            barWidth: 2

            totalLength: suggestions.contentHeight
            showLength: suggestions.height
            incrementLength: 20
        }

        delegate: Rectangle {
            width: suggestions.width
            height: 20
            property var selected: suggestions.currentIndex == index
            property var text: BASIC.suggestions.completion(modelData, prompts.cursorPosition-promptCursor.targetStart)
            color: selected ? COMMON.bg4 : (delegateMouse.containsMouse ? COMMON.bg3_5 : COMMON.bg3)

            SText {
                id: decoText
                anchors.right: parent.right
                width: contentWidth
                height: 20
                text: BASIC.suggestions.detail(modelData)
                color: width < contentWidth ? "transparent" : COMMON.fg2
                pointSize: 8.5
                rightPadding: 8
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            SText {
                id: valueText
                anchors.left: parent.left
                anchors.right: decoText.left

                height: 20
                text: BASIC.suggestions.display(modelData)
                color: BASIC.suggestions.color(modelData)
                pointSize: 8.5
                leftPadding: 5
                rightPadding: 10
                elide: Text.ElideRight

                verticalAlignment: Text.AlignVCenter
            }
            MouseArea {
                id: delegateMouse
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: true
                onPressed: {
                    suggestions.complete(parent.text)
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: {
                suggestionsScrollBar.doIncrement(wheel.angleDelta.y)
            }
        }
    }

    Rectangle {
        id: fullParams
        anchors.fill: prompts
        visible: full.visible && parameters != "" && show
        color: COMMON.bg0
        property var parameters: full.target != null ? (full.target.parameters != undefined ? full.target.parameters : "") : ""
        property var show: true

        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            border.width: 1
            border.color: COMMON.bg4
            color: "transparent"

            Rectangle {
                id: headerParams
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 25
                border.width: 1
                border.color: COMMON.bg4
                color: COMMON.bg3
                SText {
                    anchors.fill: parent
                    text: root.tr("Parameters")
                    color: COMMON.fg1_5
                    leftPadding: 5
                    verticalAlignment: Text.AlignVCenter
                }

                SIconButton {
                    visible: fullParams.visible
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 1
                    height: 23
                    width: 23
                    tooltip: root.tr("Hide Parameters")
                    icon: "qrc:/icons/eye.svg"
                    onPressed: {
                        fullParams.show = false
                    }
                }
            }

            STextArea {
                color: COMMON.bg1
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: headerParams.bottom
                anchors.bottom: parent.bottom
                anchors.margins: 1

                readOnly: true

                text: fullParams.parameters

                Component.onCompleted: {
                    GUI.setHighlighting(area.textDocument)
                }
            }
        }
    }

    AdvancedDropArea {
        id: leftDrop
        visible: !root.swap
        width: 10
        height: parent.height
        anchors.left: leftArea.left
        anchors.top: leftArea.top
        anchors.bottom: leftArea.bottom
        filters: ['application/x-qd-basic-divider']

        onDropped: {
            if(BASIC.dividerDrop(mimeData)) {
                root.swap = !root.swap
            }
        }

        Rectangle {
            visible: leftDrop.containsDrag
            width: 3
            color: COMMON.bg6
            height: parent.height
        }
    }

    AdvancedDropArea {
        id: rightDrop
        visible: root.swap
        width: 10
        height: parent.height
        anchors.right: rightArea.right
        anchors.top: rightArea.top
        anchors.bottom: rightArea.bottom
        filters: ['application/x-qd-basic-divider']

        onDropped: {
            BASIC.dividerDrop(mimeData)
        }

        Rectangle {
            visible: rightDrop.containsDrag
            anchors.right: parent.right
            width: 3
            color: COMMON.bg6
            height: parent.height
        }
    }

    SDividerVR {
        id: rightDivider
        visible: !root.swap
        minOffset: 5
        maxOffset: 300
        offset: 210

        onLimitedChanged: {
            if(limited) {
                BASIC.dividerDrag()
            }
        }
    }

    SDividerVL {
        id: leftDivider
        visible: root.swap
        minOffset: 0
        maxOffset: 300
        offset: 210

        onLimitedChanged: {
            if(limited) {
                BASIC.dividerDrag()
            }
        }
    }

    SDividerHB {
        id: promptDivider
        anchors.left: mainArea.left
        anchors.right: mainArea.right
        minOffset: 5
        maxOffset: 300
        offset: 150
    }

    Shortcut {
        sequences: COMMON.keys_generate
        onActivated: {
            if(!params.button.disabled) {
                BASIC.generate()
            }
        }
    }
    Shortcut {
        sequences: COMMON.keys_cancel
        onActivated: BASIC.cancel()
    }

    Keys.onPressed: {
        event.accepted = true
        if(event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
            case Qt.Key_V:
                BASIC.pasteClipboard()
                break;
            default:
                event.accepted = false
                break;
            }
        } else {
            switch(event.key) {
            default:
                event.accepted = false
                break;
            }
        }
    }

    ImportDialog  {
        id: importDialog
        title: root.tr("Import")
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        dim: true

        onAccepted: {
            BASIC.parameters.sync(importDialog.parser.parameters)
        }

        onClosed: {
            importDialog.parser.formatted = ""
        }

        Connections {
            target: BASIC
            function onPastedText(text) {
                importDialog.parser.formatted = text
            }
        }
    }

    GridDialog {
        id: gridDialog
        title: root.tr("Grid")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: Math.max(500, parent.width/3)
        modal: true
        dim: true

        source: BASIC.grid
        options: BASIC.grid.gridTypes()

        Connections {
            target: GUI.config
            function onUpdated() {
                gridDialog.options = BASIC.grid.gridTypes()
            }
        }

        onAccepted: {
            BASIC.grid.generateGrid(x_type, x_value, x_match, y_type, y_value, y_match)
        }

        Connections {
            target: BASIC.grid
            function onOpeningGrid() {
                gridDialog.open()
            }
        }
    }

    Keys.forwardTo: [areas, full]
}