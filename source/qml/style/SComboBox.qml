import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

ComboBox {
    id: control

    delegate: ItemDelegate {
        id: item
        width: control.width
        height: 25
        hoverEnabled: true

        contentItem: SText {
            text: modelData
            color: COMMON.fg0
            pointSize: 10
            elide: Text.ElideRight

            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: item.highlighted || control.highlightedIndex === index ? COMMON.bg2 : COMMON.bg1
        }
        highlighted: control.highlightedIndex === index
    }

    indicator: Canvas {
        id: canvas
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 12
        height: 8
        contextType: "2d"

        Connections {
            target: control.popup
            function onVisibleChanged() { canvas.requestPaint(); }
        }

        onPaint: {
            var context = getContext("2d");
            context.reset();
            context.moveTo(0, 0);
            context.lineTo(width, 0);
            context.lineTo(width / 2, height);
            context.closePath();
            context.fillStyle = control.popup.visible ? COMMON.bg5 : COMMON.bg6;
            context.fill();
        }
    }

    contentItem: SText {
        leftPadding: 10
        rightPadding: control.indicator.width + control.spacing

        text: control.displayText
        pointSize: 10.2
        color: COMMON.fg0
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 120
        implicitHeight: 30
        color: control.enabled ? COMMON.bg1 : COMMON.bg2
    }

    popup: Popup {
        y: control.height
        width: control.width
        implicitHeight: contentItem.implicitHeight+2
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: COMMON.bg0
        }
    }
}