pragma Singleton
import QtQuick 2.15

QtObject {
    readonly property var pointValue: 9.3
    readonly property var pointLabel: 9.4

    readonly property var bg0: "#1d1d1d"
    readonly property var bg1: "#242424"
    
    readonly property var bg2: "#2a2a2a"
    readonly property var bg3: "#303030"
    readonly property var bg4: "#404040"
    readonly property var bg5: "#505050"
    readonly property var bg6: "#606060"
    readonly property var bg7: "#707070"

    readonly property var fg0: "#ffffff"
    readonly property var fg1: "#eeeeee"
    readonly property var fg1_5: "#cccccc"
    readonly property var fg2: "#aaaaaa"
    readonly property var fg3: "#909090"

    // fix later lol
    readonly property var bg00: "#1a1a1a"
    readonly property var bg0_5: "#202020"
    readonly property var bg1_5: "#272727"
    readonly property var bg2_5: "#2e2e2e"
    readonly property var bg3_5: "#393939"

    readonly property var keys_basic:       ["Ctrl+1","F1"]
    readonly property var keys_models:      ["Ctrl+2","F2"]
    readonly property var keys_gallery:     ["Ctrl+3","F3"]
    readonly property var keys_settings:    ["Ctrl+0","F12"]
    readonly property var keys_generate:    ["Ctrl+Return","Ctrl+`"]
    readonly property var keys_cancel:      ["Ctrl+Backspace","Ctrl+Escape"]

    function accent(hue) {
        return Qt.hsva(hue, 0.65, 0.55, 1.0)
    }
}