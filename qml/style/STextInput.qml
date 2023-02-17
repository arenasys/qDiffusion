import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

TextInput {
    FontLoader {
        source: "qrc:/fonts/Cantarell-Regular.ttf"
    }
    FontLoader {
        source: "qrc:/fonts/Cantarell-Bold.ttf"
    }
    font.family: "Cantarell"
    font.pointSize: 10.8
    color: COMMON.fg0
    selectByMouse: true

    Component.onCompleted: {
        if(font.bold) {
            font.letterSpacing = -1.0
        }
    }
}