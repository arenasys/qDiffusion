import QtGraphicalEffects 1.15

RectangularGlow {
    required property var target
    anchors.fill: target
    glowRadius: 5
    opacity: 0.5
    spread: 0.2
    color: "black"
    cornerRadius: 10
}