import QtQuick 2.15
import QtQuick.Controls 2.15

import "../style"

SMenuBar {
    id: root
    SMenu {
        id: menu
        title: "File"
        Action {
            text: "Action"
        }
    }
    SMenu {
        title: "Edit"
        Action {
            text: "Action"
        }
    }
    SMenu {
        title: "View"
        Action {
            text: "Action"
        }
    }
    SMenu {
        title: "Help"
        Action {
            text: "Action"
        }
    }
}