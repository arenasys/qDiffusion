import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"

Item {
    id: root
    clip: true

    Media {
        id: media
        anchors.fill: parent
        source: "/run/media/pul/ssd/sd-inference-gui/image.png"
        sourceWidth: 768
        sourceHeight: 768
    }

    Item {
        id: overlay
        x: media.current.x
        y: media.current.y
        width: media.current.width
        height: media.current.height
    }

    ImageCanvas {
        id: canvas
        anchors.fill: overlay
        property var mouse_pos: []
        property var do_reset: true
        canvasSize: Qt.size(media.sourceWidth, media.sourceHeight)
        smooth: media.sourceWidth*2 < width && media.sourceHeight*2 < height ? false : true
    }

    Timer {
        interval: 17; running: true; repeat: true
        onTriggered: canvas.update()
    }

    MouseArea {
        id: mouseArea
        anchors.fill: overlay
        hoverEnabled: true

        onPressed: {
            var wf = media.sourceWidth/width
            var hf = media.sourceHeight/height
            var curr = Qt.point(mouse.x*wf, mouse.y*hf)

            canvas.mousePressed(curr)
        }

        onReleased: {
            var wf = media.sourceWidth/width
            var hf = media.sourceHeight/height
            var curr = Qt.point(mouse.x*wf, mouse.y*hf)

            canvas.mouseReleased(curr)
        }

        onPositionChanged: {
            if(mouse.buttons) {
                var wf = media.sourceWidth/width
                var hf = media.sourceHeight/height
                var curr = Qt.point(mouse.x*wf, mouse.y*hf)

                canvas.mouseDragged(curr)
            }
        }
    }
}