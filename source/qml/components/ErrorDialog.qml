import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

import "../style"
import "../components"

SDialog {
    id: dialog
    title: dialog.tr("Error")
    standardButtons: Dialog.Ok
    modal: true
    dim: true

    width: errorText.contentWidth + 50
    height: errorText.contentHeight + 80

    function tr(str, file = "ErrorDialog.qml") {
        return TRANSLATOR.instance.translate(str, file)
    }

    STextSelectable {
        id: errorText
        anchors.centerIn: parent
        padding: 5
        text: dialog.tr("Error while %1.\n%2").arg(dialog.tr(GUI.errorStatus, "Status")).arg(GUI.errorText)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        width: Math.min(errorText.implicitWidth, 500)
        wrapMode: Text.Wrap
    }

    SIconButton {
        visible: GUI.errorTrace != ""
        x: parent.width - width
        y: -height - 2
        width: 16
        height: 16
        inset: 0
        icon: "qrc:/icons/info-big.svg"
        tooltip: dialog.tr("Copy trace")
        onPressed: {
            GUI.copyError()
        }
    }

    onClosed: {
        GUI.clearError()
    }

    Connections {
        target: GUI
        function onErrorTextChanged() {
            dialog.open()
        }
    }
}

