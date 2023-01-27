import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.15

import gui 1.0

import "../../style"
import "../../components"

Rectangle {
    color: COMMON.bg0
    clip: true

    ThumbnailGrid {
        id: sources
        anchors.fill: parent
        model: Sql {
            id: sql
            query: "SELECT file FROM images ORDER BY rowid;"
        }
    }
}