
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

Row {
    id: cardSearchRow

    anchors.top: parent.top
    anchors.topMargin: 65
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: 20
    anchors.rightMargin: 20

    spacing: 8

    TextField {
        id: cardSearchField

        width: parent.width - findCardButton.width - parent.spacing
        placeholderText: "Search for a card..."

        onAccepted: studioCardModel.lookup(text)
    }

    Button {
        id: findCardButton
        text: "Find"
        enabled: !studioCardModel.loading
                 && cardSearchField.text.trim().length > 0

        onClicked: studioCardModel.lookup(cardSearchField.text)
    }
}

            Button {
                 id: chooseArtworkButton
                 text: "Choose Artwork..."
                 anchors.top: cardSearchRow.bottom
                 anchors.topMargin: 12
                 anchors.left: parent.left
                 anchors.leftMargin: 20

                 onClicked: artworkPicker.open()
            }

            
Image {
    id: artworkThumbnail
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

Column {
    anchors.top: artworkThumbnail.bottom
    anchors.topMargin: 16
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: 20
    anchors.rightMargin: 20

    spacing: 10

    Text {
        width: parent.width
        text: studioCardModel.loading
              ? "Looking up card..."
              : studioCardModel.error
        visible: studioCardModel.loading
                 || studioCardModel.error.length > 0
        color: "#E5A45B"
        wrapMode: Text.WordWrap
    }

    Text {
        width: parent.width
        text: studioCardModel.card.name || ""
        visible: text.length > 0
        color: "white"
        font.pixelSize: 18
        font.bold: true
        wrapMode: Text.WordWrap
    }

    Text {
        width: parent.width
        text: "Mana: " + (studioCardModel.card.mana_cost || "None")
        visible: Boolean(studioCardModel.card.name)
        color: "#CCCCCC"
    }

    Text {
        width: parent.width
        text: studioCardModel.card.type_line || ""
        color: "#CCCCCC"
        wrapMode: Text.WordWrap
    }

    Text {
        width: parent.width
        text: studioCardModel.card.oracle_text || ""
        color: "#CCCCCC"
        wrapMode: Text.WordWrap
    }

    Text {
        width: parent.width
        text: studioCardModel.card.power
              ? studioCardModel.card.power + " / "
                + studioCardModel.card.toughness
              : ""
        color: "#CCCCCC"
    }
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
