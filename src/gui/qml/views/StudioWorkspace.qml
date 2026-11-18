
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    // Custom artwork overrides the Scryfall default.
    property url manualArtworkUrl: ""

    readonly property string scryfallArtworkUrl:
        studioCardModel.card.art_crop || ""

    readonly property url effectiveArtworkUrl:
        manualArtworkUrl.toString().length > 0
            ? manualArtworkUrl
            : scryfallArtworkUrl

    readonly property bool hasCustomArtwork:
        manualArtworkUrl.toString().length > 0

    FileDialog {
        id: artworkPicker
        title: "Choose Card Artwork"
        fileMode: FileDialog.OpenFile

        nameFilters: [
            "Image files (*.png *.jpg *.jpeg *.webp)",
            "All files (*)"
        ]

        onAccepted: {
            workspace.manualArtworkUrl = selectedFile;
        }
    }

    // Update editable fields when Scryfall returns a card.
    Connections {
        target: studioCardModel

        function onChanged() {
            if (studioCardModel.loading) {
                // A new lookup resets the custom art override.
                workspace.manualArtworkUrl = "";
                return;
            }

            if (!studioCardModel.card.name)
                return;

            const card = studioCardModel.card;

            cardName.text = card.name || "";
            manaCost.text = card.mana_cost || "";
            typeLine.text = card.type_line || "";
            rulesText.text = card.oracle_text || "";
            flavorText.text = card.flavor_text || "";
            power.text = card.power || "";
            toughness.text = card.toughness || "";
            artist.text = card.artist || "";
            setCode.text = card.set || "";
            rarity.text = card.rarity || "";
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#101214"
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // LEFT: Card Details
        Rectangle {
            Layout.preferredWidth: 320
            Layout.minimumWidth: 270
            Layout.fillHeight: true

            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            ScrollView {
                id: editorScroll
                anchors.fill: parent
                anchors.margins: 18
                clip: true

                ScrollBar.vertical.policy:
                    ScrollBar.AsNeeded

                ColumnLayout {
                    width: editorScroll.availableWidth
                    spacing: 9

                    Text {
                        text: "Card Details"
                        color: "white"
                        font.pixelSize: 20
                        font.bold: true
                        Layout.bottomMargin: 12
                    }

                    // Card Search
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        TextField {
                            id: cardSearchField
                            Layout.fillWidth: true
                            placeholderText: "Search for a card..."

                            onAccepted:
                                studioCardModel.lookup(text)
                        }

                        Button {
                            text: studioCardModel.loading
                                  ? "..."
                                  : "Find"

                            enabled: !studioCardModel.loading
                                && cardSearchField.text.trim().length > 0

                            onClicked: studioCardModel.lookup(
                                cardSearchField.text
                            )
                        }
                    }

                    Text {
                        Layout.fillWidth: true

                        text: studioCardModel.loading
                              ? "Looking up card..."
                              : studioCardModel.error

                        visible: studioCardModel.loading
                            || studioCardModel.error.length > 0

                        color: "#E5A45B"
                        wrapMode: Text.WordWrap
                    }

                    // Card Name
                    Text {
                        text: "Name"
                        color: "#B7BDC4"
                    }

                    TextField {
                        id: cardName
                        Layout.fillWidth: true
                        placeholderText: "Card name"
                    }

                    // Mana Cost
                    Text {
                        text: "Mana Cost"
                        color: "#B7BDC4"
                    }

                    TextField {
                        id: manaCost
                        Layout.fillWidth: true
                        placeholderText: "{G}, {2}{U}, etc."
                    }

                    // Type Line
                    Text {
                        text: "Type Line"
                        color: "#B7BDC4"
                    }

                    TextField {
                        id: typeLine
                        Layout.fillWidth: true
                        placeholderText: "Creature — Elf Druid"
                    }

                    // Rules Text
                    Text {
                        text: "Rules Text"
                        color: "#B7BDC4"
                    }

                    TextArea {
                        id: rulesText
                        Layout.fillWidth: true
                        Layout.preferredHeight: 110
                        wrapMode: TextEdit.Wrap
                        placeholderText: "Card abilities..."

                        background: Rectangle {
                            color: "#303030"
                            radius: 3
                        }

                        leftPadding: 12
                        rightPadding: 12
                        topPadding: 12
                        bottomPadding: 12
                    }

                    // Flavor Text
                    Text {
                        text: "Flavor Text"
                        color: "#B7BDC4"
                    }

                    TextArea {
                        id: flavorText
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        wrapMode: TextEdit.Wrap
                        placeholderText: "Optional flavor text..."

                        background: Rectangle {
                            color: "#303030"
                            radius: 3
                        }

                        leftPadding: 12
                        rightPadding: 12
                        topPadding: 12
                        bottomPadding: 12
                    }

                    // Power / Toughness
                    Text {
                        text: "Power / Toughness"
                        color: "#B7BDC4"
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        TextField {
                            id: power
                            Layout.fillWidth: true
                            placeholderText: "Power"
                        }

                        Text {
                            text: "/"
                            color: "white"
                            font.pixelSize: 18
                        }

                        TextField {
                            id: toughness
                            Layout.fillWidth: true
                            placeholderText: "Toughness"
                        }
                    }

                    // Artist
                    Text {
                        text: "Artist"
                        color: "#B7BDC4"
                    }

                    TextField {
                        id: artist
                        Layout.fillWidth: true
                        placeholderText: "Artist name"
                    }

                    // Set and Rarity
                    Text {
                        text: "Set / Rarity"
                        color: "#B7BDC4"
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        TextField {
                            id: setCode
                            Layout.fillWidth: true
                            placeholderText: "Set"
                        }

                        TextField {
                            id: rarity
                            Layout.fillWidth: true
                            placeholderText: "Rarity"
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 14
                        Layout.bottomMargin: 8
                        color: "#34383E"
                    }

                    // ARTWORK SECTION
                    Text {
                        text: "Artwork"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 17
                    }

                    // Auto-populated Scryfall art
                    // or a manually selected image.
                    Image {
                        id: artworkPreview

                        Layout.fillWidth: true
                        Layout.preferredHeight: 190

                        source: workspace.effectiveArtworkUrl
                        fillMode: Image.PreserveAspectFit

                        visible: workspace.effectiveArtworkUrl
                            .toString().length > 0

                        asynchronous: true
                    }

                    Text {
                        Layout.fillWidth: true

                        text: artworkPreview.status === Image.Loading
                            ? "Loading artwork..."
                            : "No artwork available"

                        visible: workspace.effectiveArtworkUrl
                            .toString().length === 0
                            || artworkPreview.status === Image.Loading
                            || artworkPreview.status === Image.Error

                        color: "#8F969E"
                        font.pixelSize: 12
                    }

                    Text {
                        Layout.fillWidth: true

                        text: workspace.hasCustomArtwork
                            ? "Custom artwork selected"
                            : "Scryfall artwork • "
                              + (studioCardModel.card.artist || "Unknown artist")

                        visible: artworkPreview.status === Image.Ready

                        color: "#8F969E"
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Button {
                            text: workspace.hasCustomArtwork
                                  ? "Replace Artwork..."
                                  : "Choose Artwork..."

                            onClicked: artworkPicker.open()
                        }

                        Button {
                            text: "Use Scryfall"
                            visible: workspace.hasCustomArtwork
                                && workspace.scryfallArtworkUrl.length > 0

                            onClicked: {
                                workspace.manualArtworkUrl = "";
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true

                        text: "Edits are local to this editor for now."
                        color: "#8F969E"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.topMargin: 10
                    }
                }
            }
        }

        // CENTER: Card Preview
        Rectangle {
            Layout.fillWidth: true
            Layout.minimumWidth: 250
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

        // RIGHT: Render Settings
        Rectangle {
            Layout.preferredWidth: 280
            Layout.minimumWidth: 240
            Layout.fillHeight: true

            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            Text {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 20

                text: "Render Settings"
                color: "white"
                font.pixelSize: 18
                font.bold: true
            }
        }
    }
}
