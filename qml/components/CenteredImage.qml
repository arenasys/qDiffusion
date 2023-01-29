import QtQuick 2.15

Image {
    id: img

    property int maxWidth
    property int maxHeight
    property int sourceWidth
    property int sourceHeight

    property bool fill: false

    function sync() {
        var h = sourceHeight;
        var w = sourceWidth;

        if(h == 0 || w == 0)
            return;

        if(fill) {
            var wr = maxWidth / sourceWidth
            var hr = maxHeight / sourceHeight

            if(hr < wr) {
                h = maxHeight
                w = sourceWidth * hr
            } else {
                w = maxWidth
                h = sourceHeight * wr
            }
        } else {
            var r = 0;
            if(h > maxHeight) {
                r = maxHeight/h
                h *= r
                w *= r
            }
            if(w > maxWidth) {
                r = maxWidth/w
                h *= r
                w *= r
            }
        }

        height = parseInt(h)
        width = parseInt(w)
    }

    asynchronous: true

    onSourceChanged: {
        sync()
    }

    onStatusChanged: {
        sync()
    }

    onSourceWidthChanged: {
        sync()
    }

    onSourceHeightChanged: {
        sync()
    }

    onMaxWidthChanged: {
        sync()
    }

    onMaxHeightChanged: {
        sync()
    }
}