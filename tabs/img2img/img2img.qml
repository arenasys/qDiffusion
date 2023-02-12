import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"


Item {
    id: root

    property var size: 40
    property var spacing: 0.1
    property var hardness: 0.5

    function dropoff(x, h) {
        if(hardness == 1) {
            return 1.0
        }
        return Math.pow((Math.cos(x*Math.PI)+1)/2, 1/(2*h))
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        property var mouse_pos: []
        property var do_reset: true

        onPaint: {
            var ctx;

            ctx = getContext("2d");
            if(do_reset) {
                ctx.reset()
                do_reset = false
            }

            if(mouse_pos.length == 0) {
                return;
            }
            
            var p;
            while(mouse_pos.length != 0) {
                var p = mouse_pos.shift();

                var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, root.size/2)
                for(var x = 0; x <= 1; x += 1/10) {
                    var s = dropoff(x, root.hardness)
                    g.addColorStop(x, Qt.rgba(1, 1, 1, s));
                }
                ctx.fillStyle = g

                ctx.ellipse(p.x-root.size/2, p.y-root.size/2, root.size, root.size);
                ctx.fill();
                ctx.beginPath();
                ctx.closePath();
            }
        }
    }

    Timer {
        interval: 17; running: true; repeat: true
        onTriggered: canvas.requestPaint()
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        property var last_pos: null;

        onPressed: {
            var curr = Qt.point(mouse.x, mouse.y)
            canvas.mouse_pos.push(curr)
            last_pos = Qt.point(curr.x, curr.y)
        }

        onReleased: {
            canvas.mouse_pos = []
        }

        onPositionChanged: {
            var s = root.size*root.spacing;

            if(mouse.buttons) {
                var curr = Qt.point(mouse.x, mouse.y)
                if(last_pos == null) {
                    canvas.mouse_pos.push(curr)
                    last_pos = Qt.point(curr.x, curr.y)
                } else {
                    var last = Qt.point(last_pos.x, last_pos.y)
                    var v = Qt.point(curr.x-last.x, curr.y-last.y)
                    var m = Math.pow(v.x*v.x + v.y*v.y, 0.5)
                    var r = m/s
                    if(r < 1) {
                        return;
                    }
                    var p;
                    for(var i = 1; i <= r; i++) {
                        var f = i*s/m
                        p = Qt.point(last.x+v.x*f, last.y+v.y*f)
                        canvas.mouse_pos.push(p)
                    }
                    last_pos = Qt.point(p.x, p.y)
                }
            }
        }
    }
    Keys.onPressed: {
        event.accepted = true
        switch(event.key) {
        case Qt.Key_R:
            canvas.do_reset = true
            break;
        default:
            event.accepted = false
        }
    }
}