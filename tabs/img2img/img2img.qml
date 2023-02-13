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

    property var source: "/run/media/pul/ssd/sd-inference-gui/image.png"
    property var sourceWidth: 768
    property var sourceHeight: 768


    MovableItem {
        id: movable
        anchors.fill: parent
        itemWidth: root.sourceWidth
        itemHeight: root.sourceHeight

        ImageCanvas {
            id: canvas
            anchors.fill: parent.item
            property var mouse_pos: []
            property var do_reset: true
            source: "/run/media/pul/ssd/sd-inference-gui/image.png"
            sourceSize: Qt.size(root.sourceWidth, root.sourceHeight)
            smooth: root.sourceWidth*2 < width && root.sourceHeight*2 < height ? false : true
        }

        MouseArea {
            id: mouseArea
            anchors.fill: canvas
            hoverEnabled: true

            function getPosition(mouse) {
                var wf = root.sourceWidth/width
                var hf = root.sourceHeight/height
                return Qt.point(mouse.x*wf, mouse.y*hf)
            }

            onPressed: {
                canvas.mousePressed(getPosition(mouse))
            }

            onReleased: {
                canvas.mouseReleased(getPosition(mouse))
            }

            onPositionChanged: {
                if(mouse.buttons) {
                    canvas.mouseDragged(getPosition(mouse))
                }
            }
        }
    }

    Timer {
        interval: 17; running: true; repeat: true
        onTriggered: canvas.update()
    }
}