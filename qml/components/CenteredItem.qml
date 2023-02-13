import QtQuick 2.15

Item {
    id: itm

    property int maxWidth
    property int maxHeight
    property int itemWidth
    property int itemHeight

    property bool fill: false

    function sync() {
        var h = itemHeight;
        var w = itemWidth;

        if(h == 0 || w == 0)
            return;

        if(fill) {
            var wr = maxWidth / itemWidth
            var hr = maxHeight / itemHeight

            if(hr < wr) {
                h = maxHeight
                w = itemWidth * hr
            } else {
                w = maxWidth
                h = itemHeight * wr
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

    onItemWidthChanged: {
        sync()
    }

    onItemHeightChanged: {
        sync()
    }

    onMaxWidthChanged: {
        sync()
    }

    onMaxHeightChanged: {
        sync()
    }
}