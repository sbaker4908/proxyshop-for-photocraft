
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    property url artworkUrl: ""

    FileDialog {
        id: artworkPicker
        title: "Choose Card Artwork"
        fileMode: FileDialog.OpenFile
        nameFilters: [
            "Image files (*.png *.jpg *.jpeg *.webp)",
            "All files (*)"
        ]

        onAccepted: workspace.artworkUrl = selectedFile
    }

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

            Button {
                 id: chooseArtworkButton
                 text: "Choose Artwork..."
                  anchors.top: parent.top
                 anchors.topMargin: 70
                 anchors.left: parent.left
                 anchors.leftMargin: 20

                 onClicked: artworkPicker.open()
            }

            
Image {
    anchors.top: chooseArtworkButton.bottom
    anchors.topMargin: 16
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: 20
    anchors.rightMargin: 20

    height: 190

    source: workspace.artworkUrl
    fillMode: Image.PreserveAspectFit
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
