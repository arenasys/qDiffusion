import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import gui 1.0

Item {
    property var color: colorArea.color
    property alias trueColor: colorArea.color
    property alias trueAlpha: colorArea.opacity
    property alias trueHex: colorArea.hex

    onTrueColorChanged: {
        setColor(color)
    }

    onWidthChanged: setColor(color)
    onHeightChanged: setColor(color)

    function setColor(color) {
        var angle = (color.hsvHue+0.75) * 2*Math.PI
        var radius = color.hsvSaturation
        var lightness = color.hsvValue
        var alpha = color.a
        colorSelector.setSelection(radius, angle)
        lightnessSelector.setSelection(lightness)
        alphaSelector.setSelection(alpha)
    }

    Component.onCompleted: {
        setColor(Qt.rgba(1,1,1,1))
    }
    
    Rectangle {
        anchors.left: colorArea.left
        anchors.top: colorArea.top
        anchors.margins: -2.5
        width: 2*Math.floor(colorArea.width/2) + 5
        height: width
        radius: width/2
        color: COMMON.bg4
    }

    Rectangle {
        id: colorAreaBg
        anchors.left: colorArea.left
        anchors.top: colorArea.top
        anchors.margins: -1
        width: 2*Math.floor(colorArea.width/2) + 2
        height: width
        radius: width/2
        color: "black"
    }

    ColorRadial {
        id: colorArea

        lightness: lightnessSelector.selectedLightness
        angle: colorSelector.selectedAngle
        radius: colorSelector.selectedRadius
        alpha: alphaSelector.selectedAlpha

        property var areaCenter: Qt.point(width/2, height/2)
        property var areaRadius: Math.min(width, height)/2

        anchors.top: parent.top
        anchors.bottom: alphaArea.top
        anchors.right: lightnessArea.left
        anchors.left: parent.left
        anchors.margins: 6
        anchors.topMargin: 7
        anchors.leftMargin: 7
    }
    
    TransparencyShader {
        anchors.fill: selectedColor
        styled: false
    }

    Rectangle {
        id: selectedColor
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 5
        color: colorArea.color
        width: 20
        height: 20
        border.color: "black"
        border.width: 2

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

    }

    Rectangle {
        id: lightnessArea

        property var displayA: Qt.hsva(colorArea.color.hsvHue, colorArea.color.hsvSaturation, 0.0, 1.0)
        property var displayB: Qt.hsva(colorArea.color.hsvHue, colorArea.color.hsvSaturation, 1.0, 1.0)
        anchors.top: parent.top
        anchors.bottom: selectedColor.top
        anchors.right: parent.right
        anchors.margins: 5
        border.color: "black"
        border.width: 2

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

        width: 20
        property var inset: 10.0/height
        gradient: Gradient {
            GradientStop { position: 0.0; color: lightnessArea.displayA }
            GradientStop { position: lightnessArea.inset; color: lightnessArea.displayA }
            GradientStop { position: 1-lightnessArea.inset; color: lightnessArea.displayB }
            GradientStop { position: 1.0; color: lightnessArea.displayB }
        }
    }

    TransparencyShader {
        anchors.fill: alphaArea
        styled: false
    }

    Rectangle {
        id: alphaArea
        property var display: Qt.rgba(colorArea.color.r, colorArea.color.g, colorArea.color.b, 1.0)
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.right: selectedColor.left
        anchors.margins: 5
        border.color: "black"
        border.width: 2
        height: 20

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

        property var inset: 10.0/width
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: alphaArea.inset; color: "transparent" }
            GradientStop { position: 1-alphaArea.inset; color: alphaArea.display }
            GradientStop { position: 1.0; color: alphaArea.display }
        }
    }

    Rectangle {
        id: colorSelector
        property var selectedRadius: 0.0
        property var selectedAngle: 0.0
        width: 10
        height: 10
        color: "white"
        border.color: "black"
        border.width: 2
        anchors.centerIn: colorArea

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

        function setSelection(radius, angle) {
            var center = colorArea.areaCenter

            colorSelector.anchors.centerIn = undefined
            colorSelector.x = 2 + center.x - Math.cos(angle)*radius*colorArea.areaRadius
            colorSelector.y = 2 + center.y - Math.sin(angle)*radius*colorArea.areaRadius

            colorSelector.selectedAngle = ((angle/(2*Math.PI)) + 1.25) % 1.0
            colorSelector.selectedRadius = radius
        }
    }

    MouseArea {
        id: colorMouse
        anchors.fill: colorArea
        preventStealing: true

        function set(mouse) {
            var center = colorArea.areaCenter
            var pos = Qt.point(center.x - mouse.x, center.y - mouse.y)
            var radius = Math.min(colorArea.areaRadius, Math.pow(pos.x*pos.x + pos.y*pos.y, 0.5))/colorArea.areaRadius
            var angle = Math.atan2(pos.y, pos.x)

            if(radius < 0.1) {
                radius = 0
            }

            colorSelector.setSelection(radius, angle)
        }

        onPressed: set(mouse)
        onPositionChanged: {
            if(pressed) {
                set(mouse)
            }
        }
    }
    
    Rectangle {
        id: lightnessSelector
        property var selectedLightness: 0.5
        width: 10
        height: 10
        color: "white"
        border.color: "black"
        border.width: 2
        anchors.centerIn: lightnessArea

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

        function setSelection(lightness) {
            var margin = lightnessArea.height * lightnessArea.inset
            lightnessSelector.anchors.centerIn = undefined
            lightnessSelector.y = ((lightnessArea.height - 2*margin) * lightness) + margin
            lightnessSelector.x = lightnessArea.x + lightnessArea.width/2 - 5
            lightnessSelector.selectedLightness = lightness
        }
    }

    MouseArea {
        id: lightnessMouse
        anchors.fill: lightnessArea
        preventStealing: true

        function set(mouse) {
            var margin = lightnessArea.height * lightnessArea.inset
            var lightness = (mouse.y - margin) / (lightnessArea.height - 2*margin)

            lightness = Math.min(1, Math.max(0, lightness))

            lightnessSelector.setSelection(lightness)
        }

        onPressed: set(mouse)
        onPositionChanged: {
            if(pressed) {
                set(mouse)
            }
        }
    }

    Rectangle {
        id: alphaSelector
        property var selectedAlpha: 0.5
        width: 10
        height: 10
        color: "white"
        border.color: "black"
        border.width: 2
        anchors.centerIn: alphaArea

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.width: 1
            border.color: COMMON.bg4
        }

        function setSelection(alpha) {
            var margin = alphaArea.width * alphaArea.inset
            alphaSelector.anchors.centerIn = undefined
            alphaSelector.selectedAlpha = alpha
            alphaSelector.x = ((alphaArea.width - 2*margin) * alpha) + margin
            alphaSelector.y = alphaArea.y + alphaArea.height/2 - 5
        }
    }

    MouseArea {
        id: alphaMouse
        anchors.fill: alphaArea
        preventStealing: true

        function set(mouse) {
            var margin = alphaArea.width * alphaArea.inset
            var alpha = (mouse.x - margin) / (alphaArea.width - 2*margin)

            alpha = Math.min(1, Math.max(0, alpha))

            alphaSelector.setSelection(alpha)
        }

        onPressed: set(mouse)
        onPositionChanged: {
            if(pressed) {
                set(mouse)
            }
        }
    }
}