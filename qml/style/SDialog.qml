import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.15

import gui 1.0

Dialog {
    id: dialog
    anchors.centerIn: parent
    width: 300
    dim: false

    padding: 5

    background: Item {
        SGlow {
            target: bg
            cornerRadius: 2
            glowRadius: 15
            spread: 0.05
        }

        Rectangle {
            id: bg
            anchors.fill: parent
            color: COMMON.bg4_5
        }
    }

    header: Item {
        
        implicitHeight: 20
        Rectangle {
            anchors.fill: parent
            color: COMMON.bg4
        }
        SText {
            color: COMMON.fg2
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: dialog.title
            font.pointSize: 9
            font.bold: true
        }
    }

    contentItem: Rectangle {
        color: COMMON.bg5
    }

    spacing: 0
    verticalPadding: 0

    footer: Rectangle {
        implicitWidth: parent.width
        implicitHeight: 35
        color: COMMON.bg4
        DialogButtonBox {
            anchors.centerIn: parent
            standardButtons: dialog.standardButtons

            spacing: 5

            background: Item {
                implicitHeight: 25
            }

            delegate: Button {
                id: control
                implicitHeight: 25

                contentItem: SText {
                    color: COMMON.fg1
                    text: control.text
                    font.pointSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 1
                    color: COMMON.bg5
                }
            }

            onAccepted: dialog.accept()
            onRejected: dialog.reject()
        }
    }
}