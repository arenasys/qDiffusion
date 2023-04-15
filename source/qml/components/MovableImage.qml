import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

import "../style"

MovableItem {
    id: root
    property string source
    property int sourceWidth
    property int sourceHeight
    property bool thumbnailOnly: false

    itemWidth: sourceWidth
    itemHeight: sourceHeight

    clip: true

    SGlow {
        visible: root.item.width > 0
        target: root.item
    }

    LoadingSpinner {
        anchors.fill: thumb
        running: thumb.status !== Image.Ready
    }

    Image {
        id: thumb
        anchors.fill: root.item
        visible: thumbnailOnly || full.status != Image.Ready
        asynchronous: !GUI.isCached(root.source)
        source: (GUI.isCached(root.source) ? "image://sync/" : "image://async/") + root.source
        cache: false
    }

    Image {
        id: full
        anchors.fill: root.item
        asynchronous: true
        source: thumbnailOnly || thumb.status != Image.Ready || root.source == "" ? "" : "file:///"  + root.source
        visible: full.status == Image.Ready && thumb.status == Image.Ready
        smooth: root.sourceWidth*2 < width && root.sourceHeight*2 < height ? false : true
        mipmap: true
        cache: false
    }

    onSourceChanged: {
        reset()
    }

    Drag.hotSpot.x: x
    Drag.hotSpot.y: y
    Drag.dragType: Drag.Automatic
    Drag.mimeData: { "text/uri-list": "file:///" + source }
    Drag.active: mouse.drag.active
}