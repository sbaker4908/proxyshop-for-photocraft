// Themed push button.

pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls

Button {
    id: control

    required property SystemPalette systemPalette
    property color bgColor: "transparent"

    // Non-intercepting hover handler: cursor only, never steals clicks.
    HoverHandler {
        enabled: control.enabled
        cursorShape: Qt.PointingHandCursor
    }

    background: Rectangle {
        implicitHeight: 30
        implicitWidth: control.contentItem.implicitWidth
        color: control.bgColor

        Rectangle {
            anchors.fill: parent
            visible: control.enabled && (control.down || control.hovered)
            opacity: control.down ? 0.1 : 0.05
            color: control.systemPalette.text
        }
    }
}
