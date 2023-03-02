import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

TextArea {
    readOnly: true
    selectByMouse: true
    
    FontLoader {
        source: "qrc:/fonts/Cantarell-Regular.ttf"
    }
    FontLoader {
        source: "qrc:/fonts/Cantarell-Bold.ttf"
    }
    FontLoader {
        source: "qrc:/fonts/SourceCodePro-Regular.ttf"
    }
    property var monospace: false
    font.family: monospace ? "Source Code Pro" : "Cantarell"
    font.pointSize: 10.8
    color: COMMON.fg0

    Component.onCompleted: {
        if(font.bold) {
            font.letterSpacing = -1.0
        }
    }
}