import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property var running: false
    property var value: 0.0
    property var minValue: 0.0
    property var maxValue: 1.0
    property var duration: 1000
    property var fps: 30

    property var loop: false
    property var pulse: false

    property var rate: Math.floor(1000/fps)

    function restart() {
        value = minValue
        if(!running) {
            running = true
        }
    }

    function start() {
        if(!running) {
            restart()
        }
    }

    function stop() {
        if(running) {
            running = false
        }
    }

    Timer {
        id: ticker
        interval: root.rate
        repeat: true
        running: root.running && !root.pulse
        onTriggered: {
            var s = (root.maxValue - root.minValue)
            var d = (ticker.interval/root.duration) * s
            var v = root.value + d
            if(v > root.maxValue) {
                if(root.loop) {
                    while(v > root.maxValue) {
                        v -= s
                    }
                } else {
                    v = root.maxValue
                    root.running = false
                }
            }
            root.value = v
        }
    }

    Timer {
        id: pulser
        interval: root.rate
        repeat: true
        running: root.running && root.pulse
        property var reverse: false

        onRunningChanged: {
            reverse = false
        }

        onTriggered: {
            var s = (root.maxValue - root.minValue)
            var d = (ticker.interval/root.duration) * s * 2
            var v = root.value
            if (reverse) {
                v -= d
                if(v < root.minValue) {
                    root.value = root.minValue
                    root.running = false
                    return
                }
            } else {
                v += d
                if(v > root.maxValue) {
                    root.value = root.maxValue
                    pulser.reverse = true
                    return
                }
            }
            root.value = v
        }
    }
}