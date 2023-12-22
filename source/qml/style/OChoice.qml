import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    id: root
    property var label: "Label"
    property var tooltip: ""
    property alias model: control.model
    property var mini: height == 20
    property var value: control.currentIndex == -1 ? overloadValue : (control.model.length == 0 ? "" : control.model[control.currentIndex])
    property alias currentIndex: control.currentIndex

    property var placeholder: root.value == ""
    property var placeholderValue: "None"
    property var emptyValue: ""
    property var overloadValue: ""

    property var disabled: false
    property var overlay: root.disabled
    property var padded: true
    property var bottomPadded: false
    property var rightPadding: padded

    property alias control: control
    property alias delegate: control.delegate

    property variant bindMap: null
    property variant bindMapModel: bindMap
    property variant bindMapCurrent: bindMap
    property var bindKeyCurrent: null
    property var bindKeyModel: null
    property var bindKeyLabel: null

    property var binding: root.bindMapCurrent != null && root.bindKeyCurrent != null && root.bindMapModel != null && root.bindKeyModel != null

    property var original
    property var entries

    property alias popupHeight: control.popupHeight

    signal doUpdate()

    onDoUpdate: {
        root.update()
    }

    function decoration(value) {
        return ""
    }

    function display(text) {
        return text
    }

    function label_display(text) {
        return text
    }

    function expandModel(model) {
        return model
    }

    function filterModel(model) {
        return model
    }

    function searchModel(model) {
        var re = new RegExp(searchBox.text, "i");
        return model.filter((entry) => re.test(entry));
    }

    function underlineOption(text, search) {
        var re = new RegExp("("+search+")", "i");
        return text.replace(re, "<u>$1</u>");
    }

    function setCurrent(c, m, all_m) {
        var i = root.model.indexOf(c);

        if(i == -1 && all_m.includes(c)) {
            root.overloadValue = c
        } else {
            root.overloadValue = root.emptyValue
        }
        root.currentIndex = i
    }

    function update() {
        if(root.binding) {
            var all_m = expandModel(root.bindMapModel.get(root.bindKeyModel));
            var m = searchModel(filterModel(all_m));
            var c = root.bindMapCurrent.get(root.bindKeyCurrent);

            if(m != root.model) {
                var diff = (m == null || root.model == null || root.model.length != m.length)
                root.model = m;

                root.setCurrent(c, m, all_m);

                if(diff) {
                    root.optionsChanged()
                }
            } else {
                root.setCurrent(c, m, all_m);
            }
            if(root.bindKeyLabel != null) {
                root.label = root.bindMap.get(root.bindKeyLabel);
            }
        } else {
            var c = root.value
            var m = searchModel(filterModel(root.original));
            root.model = m
            root.setCurrent(c, m, root.original);
        }
    }

    onBindMapChanged: {
        bindMapModel = bindMap
        bindMapCurrent = bindMap
        root.update()
    }

    onBindKeyCurrentChanged: {
        if(binding) {
            root.update()
        }
    }

    onBindKeyModelChanged: {
        if(binding) {
            root.update()
        }
    }

    onBindMapModelChanged: {
        if(bindMap == null && binding) {
            root.update()
        }
    }

    onBindMapCurrentChanged: {
        if(bindMap == null && binding) {
            root.update()
        }
    }

    Connections {
        target: bindMapModel
        function onUpdated(key) {
            if(key == bindKeyCurrent || key == bindKeyLabel || key == bindKeyModel) {
                root.update()
            }
        }
    }

    Connections {
        target: bindMapCurrent
        function onUpdated(key) {
            if(bindMapCurrent != bindMapModel) {
                if(key == bindKeyCurrent || key == bindKeyLabel || key == bindKeyModel) {
                    root.update()
                }
            }
        }
    }

    onEntriesChanged: {
        root.model = root.entries.slice();
        root.original = root.entries.slice();
    }

    Component.onCompleted: {
        if(root.binding) {
            if (root.model) {
                root.original = root.model.slice();
            }

            var all_m = expandModel(root.bindMapModel.get(root.bindKeyModel));
            var m = searchModel(filterModel(all_m));
            var c = root.bindMapCurrent.get(root.bindKeyCurrent);
            root.model = m;

            root.setCurrent(c, m, all_m);

            if(root.bindKeyLabel != null) {
                root.label = root.bindMap.get(root.bindKeyLabel);
            }
        }
    }

    onSelected: {
        if(root.binding && root.value != "") {
            var all_m = expandModel(root.bindMapModel.get(root.bindKeyModel));
            if(all_m.includes(root.value)) {
                root.bindMapCurrent.set(root.bindKeyCurrent, root.value);
            }
        }
    }

    signal tryEnter()
    signal enter()
    signal exit()
    signal contextMenu()
    signal selected()
    signal optionsChanged()

    SToolTip {
        id: infoToolTip
        visible: !control.popup.opened && !disabled && tooltip != "" && mouseArea.containsMouse
        delay: 200
        text: root.tooltip != undefined ? root.tooltip : ""
    }

    TextInput {
        id: searchBox
        anchors.fill: parent
        anchors.margins: 1
        clip: true
        onTextChanged: {
            root.update()
        }
    }

    ComboBox {
        id: control
        anchors.fill: parent
        anchors.margins: root.padded ? 2 : 0
        anchors.topMargin: root.padded ? (root.bottomPadded ? 0 : 2) : 0
        anchors.bottomMargin: root.padded ? (root.bottomPadded ? 2 : 0) : 0
        anchors.rightMargin: root.rightPadding ? 2 : 0
        focusPolicy: Qt.NoFocus
        currentIndex: 0

        property var popupHeight: 300

        function selected() {
            root.selected()
        }

        delegate: Rectangle {
            width: control.popup.width
            height: 22
            color: delegateMouse.containsMouse ? COMMON.bg4 : (index == currentIndex || (index == 0 && control.currentIndex == -1) ? COMMON.bg3_5 : COMMON.bg3)
            SText {
                id: decoText
                anchors.right: parent.right
                width: contentWidth
                height: 22
                text: root.decoration(modelData)
                color: width < contentWidth ? "transparent" : COMMON.fg2
                pointSize:  8.5
                rightPadding: 8
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            SText {
                id: valueText
                anchors.left: parent.left
                anchors.right: decoText.left

                height: 22
                text: root.underlineOption(root.display(modelData), searchBox.text)
                color: COMMON.fg0
                pointSize:  8.5
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
                    control.currentIndex = index
                    control.selected()
                    control.popup.close()
                }
            }
        }

        indicator: Rectangle {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 10
            color: COMMON.bg4
            Canvas {
                id: canvas
                renderStrategy: Canvas.Cooperative
                anchors.fill: parent
                contextType: "2d"

                Connections {
                    target: control.popup
                    function onVisibleChanged() { canvas.requestPaint(); }
                }

                Connections {
                    target: root
                    function onVisibleChanged() { canvas.requestPaint(); }
                }

                onPaint: {
                    var context = getContext("2d");
                    var ox = width/2
                    var oy = height/2
                    var dx = root.mini ? 2.5 : 3.25
                    var dy = control.popup.visible ? -dx : dx

                    context.reset();
                    context.moveTo(ox-dx, oy-dy);
                    context.lineTo(ox+dx, oy-dy);
                    context.lineTo(ox, oy+dy);
                    context.closePath();
                    context.fillStyle = COMMON.bg6;
                    context.fill();
                }
            }
        }

        contentItem: Item {
            clip: true
            SText {
                id: labelText
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                leftPadding: 5
                text: root.label_display(root.label)
                pointSize: root.mini ? 7.85 : COMMON.pointLabel
                color: COMMON.fg1_5
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                monospace: false
            }
            
            SText {
                id: valueText
                anchors.right: parent.right
                anchors.left: labelText.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                leftPadding: 5
                rightPadding: 7

                text: root.placeholder ? root.placeholderValue : root.display(root.value)
                pointSize: root.mini ? 7.7 : COMMON.pointValue
                color: root.placeholder ? COMMON.fg2 : COMMON.fg0
                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }

        background: Rectangle {
            implicitWidth: 120
            implicitHeight: 30
            color: COMMON.bg2_5
            border.color: COMMON.bg4
            border.width: 1
        }

        popup: Popup {
            y: control.height
            width: Math.max(100, control.width)
            implicitHeight: Math.min(control.popupHeight, contentItem.implicitHeight+2)
            padding: 2
            closePolicy: Popup.NoAutoClose

            onOpenedChanged: {
                if(opened) {
                    searchBox.text = ""
                    root.enter()
                } else {
                    root.exit()
                }
            }

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight+2
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: SScrollBarV {
                    id: scrollBar
                    padding: 0
                    barWidth: 2

                    totalLength: parent.contentHeight
                    showLength: parent.height
                    increment: 1/Math.ceil(parent.implicitHeight/22)
                }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton
                    onWheel: {
                        scrollBar.doIncrement(wheel.angleDelta.y)
                    }
                }
            }

            background: Rectangle {
                color: COMMON.bg0
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    color: COMMON.bg4
                }
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if(mouse.button == Qt.RightButton) {
                root.contextMenu()
            } else {
                root.forceActiveFocus()
                root.tryEnter()
                if(control.popup.opened) {
                    control.popup.close()
                } else if (!root.disabled && !root.placeholder) {
                    control.popup.open()
                }
            }
        }
    }

    Rectangle {
        anchors.fill: control
        visible: root.overlay
        color: "#90101010"
    }

    Rectangle {
        anchors.fill: control
        visible: root.disabled
        color: "#c0101010"
    }
    
    Keys.onPressed: {
        event.accepted = true
        
        switch(event.key) {
        case Qt.Key_Up:
            if(control.currentIndex > 0) {
                control.currentIndex -= 1
            }
            break;
        case Qt.Key_Down:
            if(control.currentIndex < control.count-1) {
                if(control.currentIndex == -1) {
                    control.currentIndex = 1
                } else {
                    control.currentIndex += 1
                }
            }
            break;
        case Qt.Key_Return:
            if(searchBox.text && control.model.length > 0 && control.currentIndex == -1) {
                control.currentIndex = 0
            }
            control.popup.close()
            break;
        default:
            event.accepted = false
            break;
        }
    }

    Keys.forwardTo: [searchBox]
}