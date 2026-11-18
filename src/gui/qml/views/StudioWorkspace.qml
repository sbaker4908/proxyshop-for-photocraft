
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: workspace

    Rectangle {
        anchors.fill: parent
        color: "#101214"
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // Left panel: Card Editor
        Rectangle {
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            Text {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 20
                text: "Card Details"
                color: "#FFFFFF"
                font.pixelSize: 18
                font.bold: true
            }
        }

        // Center panel: Card Preview
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            Text {
                anchors.centerIn: parent
                text: "Card Preview"
                color: "#888888"
                font.pixelSize: 22
            }
        }

        // Right panel: Render Controls
        Rectangle {
            Layout.preferredWidth: 280
            Layout.fillHeight: true
            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            Text {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 20
                text: "Render Settings"
                color: "#FFFFFF"
                font.pixelSize: 18
                font.bold: true
            }
        }
    }
}
