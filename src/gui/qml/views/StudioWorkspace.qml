
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    // ==================================
    // WORKSPACE STATE
    // ==================================

    property url manualArtworkUrl: ""
    property url previewCardUrl: ""

    readonly property string scryfallArtworkUrl:
        studioCardModel.card.art_crop || ""

    readonly property url effectiveArtworkUrl:
        manualArtworkUrl.toString().length > 0
            ? manualArtworkUrl
            : scryfallArtworkUrl

    readonly property bool hasCustomArtwork:
        manualArtworkUrl.toString().length > 0

    readonly property int selectedTemplateIndex:
        templateListModel.selected_index

    readonly property string selectedTemplateName:
        selectedTemplateIndex >= 0
            ? (templateListModel.get_data(
                selectedTemplateIndex, "name") || "")
            : ""

    readonly property bool selectedTemplateInstalled:
        selectedTemplateIndex >= 0
            ? Boolean(templateListModel.get_data(
                selectedTemplateIndex, "is_installed"))
            : false

    readonly property string selectedTemplatePreviewUrl:
        selectedTemplateIndex >= 0
            ? (templateListModel.get_data(
                selectedTemplateIndex, "img") || "")
            : ""

    // ==================================
    // FILE PICKERS
    // ==================================

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

    FileDialog {
        id: renderPicker
        title: "Open Finished Card"
        fileMode: FileDialog.OpenFile
        currentFolder: filePathModel.out_directory

        nameFilters: [
            "Rendered cards (*.png *.jpg *.jpeg *.webp)",
            "All files (*)"
        ]

        onAccepted: {
            workspace.previewCardUrl = selectedFile;
        }
    }

    // ==================================
    // SCRYFALL CARD DATA
    // ==================================

    Connections {
        target: studioCardModel

        function onChanged() {
            if (studioCardModel.loading) {
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

        // ==================================
        // LEFT PANEL: CARD DETAILS
        // ==================================

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
                                ? "..." : "Find"

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

                    // Name
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

                    // Set / Rarity
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

                    // Artwork
                    Text {
                        text: "Artwork"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 17
                    }

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
                            : artworkPreview.status === Image.Error
                                ? "Could not load artwork"
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
                              + (studioCardModel.card.artist
                                  || "Unknown artist")

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

        // ==================================
        // CENTER PANEL: CARD PREVIEW
        // ==================================

        Rectangle {
            Layout.fillWidth: true
            Layout.minimumWidth: 250
            Layout.fillHeight: true

            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12

                Text {
                    text: "Card Preview"
                    color: "white"
                    font.pixelSize: 20
                    font.bold: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Button {
                        text: "Open Render..."
                        onClicked: renderPicker.open()
                    }

                    Button {
                        text: "Output Folder"
                        onClicked: Qt.openUrlExternally(
                            filePathModel.out_directory
                        )
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    radius: 8
                    color: "#141619"
                    border.color: "#34383E"
                    clip: true

                    Image {
                        id: renderedCardImage

                        anchors.fill: parent
                        anchors.margins: 20

                        source: workspace.previewCardUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false

                        visible: workspace.previewCardUrl
                            .toString().length > 0
                    }

                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 48

                        text: renderedCardImage.status === Image.Error
                            ? "Could not load the selected card."
                            : renderedCardImage.status === Image.Loading
                                ? "Loading rendered card..."
                                : "Open a completed render to preview it here."

                        visible: renderedCardImage.status !== Image.Ready

                        color: "#8F969E"
                        font.pixelSize: 16
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Displays the finished card image, not the source artwork."
                    color: "#8F969E"
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }

        // ==================================
        // RIGHT PANEL: RENDER SETTINGS
        // ==================================

        Rectangle {
            Layout.preferredWidth: 300
            Layout.minimumWidth: 240
            Layout.fillHeight: true

            radius: 10
            color: "#1B1E22"
            border.color: "#34383E"

            ScrollView {
                id: renderSettingsScroll
                anchors.fill: parent
                anchors.margins: 18
                clip: true

                ScrollBar.vertical.policy:
                    ScrollBar.AsNeeded

                ColumnLayout {
                    width: renderSettingsScroll.availableWidth
                    spacing: 12

                    Text {
                        text: "Render Settings"
                        color: "white"
                        font.pixelSize: 20
                        font.bold: true
                        Layout.bottomMargin: 12
                    }

                    Text {
                        text: "Frame Template"
                        color: "white"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    ComboBox {
                        id: templatePicker
                        Layout.fillWidth: true

                        model: templateListModel
                        textRole: "name"

                        currentIndex:
                            templateListModel.selected_index

                        onActivated: function(index) {
                            if (templateListModel.get_data(
                                    index, "is_installed")) {

                                templateListModel.selected_index = index;

                            } else {
                                currentIndex =
                                    templateListModel.selected_index;
                            }
                        }

                        delegate: ItemDelegate {
                            required property int index
                            required property string name
                            required property bool is_installed

                            width: templatePicker.width

                            text: name + (
                                is_installed
                                    ? ""
                                    : " (not installed)"
                            )

                            enabled: is_installed

                            highlighted:
                                templatePicker.highlightedIndex === index
                        }
                    }

                    Text {
                        Layout.fillWidth: true

                        text: workspace.selectedTemplateInstalled
                            ? "Installed and available"
                            : "Template not installed"

                        color: workspace.selectedTemplateInstalled
                            ? "#72D59A"
                            : "#E5A45B"

                        font.pixelSize: 12
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 275

                        radius: 8
                        color: "#141619"
                        border.color: "#34383E"

                        Image {
                            anchors.fill: parent
                            anchors.margins: 12

                            source:
                                workspace.selectedTemplatePreviewUrl

                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "No template preview available"

                            visible:
                                workspace.selectedTemplatePreviewUrl.length === 0

                            color: "#8F969E"
                            font.pixelSize: 12
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: workspace.selectedTemplateName
                        color: "white"
                        font.pixelSize: 15
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 12
                        color: "#34383E"
                    }

                    Text {
                        Layout.fillWidth: true

                        text: "Template selection is shared with "
                              + "Proxyshop's rendering engine."

                        color: "#8F969E"
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        Layout.fillWidth: true

                        text: "Studio rendering will be connected "
                              + "in an upcoming development step."

                        color: "#8F969E"
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }
}
