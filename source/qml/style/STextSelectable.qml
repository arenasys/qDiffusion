import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

TextEdit {
    FontLoader {
        source: "qrc:/fonts/Cantarell-Regular.ttf"
    }
    FontLoader {
        source: "qrc:/fonts/Cantarell-Bold.ttf"
    }
    FontLoader {
        source: "qrc:/fonts/SourceCodePro-Regular.ttf"
    }
    
    property var pointSize: 10.8
    property var monospace: false

    font.family: monospace ? "Source Code Pro" : "Cantarell"
    font.pointSize: pointSize * COORDINATOR.scale
    color: COMMON.fg0
    readOnly: true
    wrapMode: Text.WordWrap
    selectByMouse: true
    Component.onCompleted: {
        if(font.bold) {
            font.letterSpacing = -1.0
        }
    }
}