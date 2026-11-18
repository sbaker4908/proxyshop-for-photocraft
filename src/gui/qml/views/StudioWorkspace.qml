import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    // The Studio workflow intentionally remains separate from the legacy Render button.
    property url manualArtworkUrl: ""
    property url previewCardUrl: ""

    // Save the exact form state submitted for the latest Studio render.
    // These are local UI snapshots, not an attempt to inspect the exported JPG.
    property string pendingRenderSignature: ""
    property string lastRenderedSignature: ""

    readonly property string currentEditorSignature: JSON.stringify([
        studioCardModel.card.art_crop || "",
        studioCardModel.card.name || "",
        studioCardModel.card.set || "",
        cardName.text, manaCost.text, typeLine.text,
        rulesText.text, flavorText.text,
        power.text, toughness.text, artist.text,
        setCode.text, rarity.text,
        effectiveArtworkUrl.toString(),
        selectedTemplateName,
        selectedTemplateIndex >= 0
            ? (templateListModel.get_data(selectedTemplateIndex, "plugin_id") || "")
            : ""
    ])

    // The queue reports whether this specific preview came from Studio.
    // Compare that provenance and the submitted form snapshot instead of
    // comparing URL strings (which Qt may normalize differently).
    readonly property bool previewIsCurrent:
        renderedCardImage.status === Image.Ready
        && lastRenderedSignature.length > 0
        && lastRenderedSignature === currentEditorSignature
        && studioRenderPreviewModel.preview_is_studio

    readonly property string previewBadgeText:
        studioRenderModel.busy ? "RENDERING"
        : renderedCardImage.status !== Image.Ready ? "NO PREVIEW"
        : previewIsCurrent ? "CURRENT PREVIEW" : "NEEDS RENDER"

    readonly property string previewBadgeBackground:
        previewBadgeText === "CURRENT PREVIEW" ? "#26372f"
        : previewBadgeText === "NEEDS RENDER" ? "#373127"
        : previewBadgeText === "RENDERING" ? "#2c353c" : "#30363b"

    readonly property string previewBadgeForeground:
        previewBadgeText === "CURRENT PREVIEW" ? "#b4d8c3"
        : previewBadgeText === "NEEDS RENDER" ? "#dec8a2"
        : previewBadgeText === "RENDERING" ? "#b7cdd9" : "#aab3bb"

    readonly property string scryfallArtworkUrl: studioCardModel.card.art_crop || ""
    readonly property bool hasCustomArtwork: manualArtworkUrl.toString().length > 0
    readonly property url effectiveArtworkUrl: hasCustomArtwork
        ? manualArtworkUrl : scryfallArtworkUrl

    // Uses the same template selection as the existing Templates tab.
    readonly property int selectedTemplateIndex: templateListModel.selected_index
    readonly property string selectedTemplateName: selectedTemplateIndex >= 0
        ? (templateListModel.get_data(selectedTemplateIndex, "name") || "") : ""
    readonly property bool selectedTemplateInstalled: selectedTemplateIndex >= 0
        ? Boolean(templateListModel.get_data(selectedTemplateIndex, "is_installed")) : false
    readonly property string selectedTemplatePreviewUrl: selectedTemplateIndex >= 0
        ? (templateListModel.get_data(selectedTemplateIndex, "img") || "") : ""

    // These are readiness checks, not guesses about render progress.
    readonly property string missingRequirement: {
        if (studioCardModel.loading) return "Looking up card details...";
        if (!studioCardModel.card.name) return "Find a card to get started.";
        if (studioCardModel.card.studio_compatible === "no") return "Use the original Render button for this special layout.";
        if (cardName.text.trim().length === 0) return "Enter a card name.";
        if (typeLine.text.trim().length === 0) return "Enter a type line.";
        if (effectiveArtworkUrl.toString().length === 0) return "Choose artwork for this card.";
        if (!selectedTemplateInstalled) return "Select an installed template.";
        return "";
    }
    readonly property bool canRender: !studioRenderModel.busy && missingRequirement.length === 0

    // UI-only status tones: an entire subtle panel replaces icon-based status.
    // Readiness takes priority over an older completed render, so missing
    // information is never presented as ready merely because a past job finished.
    readonly property string renderStatusTone:
        studioRenderModel.phase === "error" ? "error"
        : studioRenderModel.busy ? "working"
        : missingRequirement.length > 0 ? "attention"
        : "success"

    // Keep the indicator succinct. Detailed readiness checks still govern
    // whether Render Card is enabled; only their visual presentation changes.
    readonly property string renderStatusTitle:
        studioRenderModel.phase === "error" ? "Render failed"
        : studioRenderModel.busy
            ? (studioRenderModel.status || "Rendering in PhotoCraft...")
        : missingRequirement.length > 0 ? "Not ready to render"
        : studioRenderModel.phase === "complete" ? "Render complete"
        : "Ready to render"

    readonly property color accent: "#44bf7e"
    readonly property color muted: "#9da5ae"
    readonly property color stroke: "#373e43"

    function sendRender() {
        if (!canRender)
            return;
        // Capture BEFORE handing off to the asynchronous PhotoCraft queue.
        pendingRenderSignature = currentEditorSignature;
        studioRenderModel.render_card({
            name: cardName.text,
            mana_cost: manaCost.text,
            type_line: typeLine.text,
            oracle_text: rulesText.text,
            flavor_text: flavorText.text,
            power: power.text,
            toughness: toughness.text,
            artist: artist.text,
            set: setCode.text,
            rarity: rarity.text,
            manual_artwork: hasCustomArtwork ? manualArtworkUrl.toString() : ""
        });
    }

    // Small reusable controls keep styling consistent across the editor.
    component StudioField: TextField {
        id: field
        font.pixelSize: 13
        color: "#f2f4f5"
        placeholderTextColor: "#89919a"
        selectionColor: "#23784e"
        selectedTextColor: "white"
        leftPadding: 11
        rightPadding: 11
        implicitHeight: 39
        HoverHandler {
            enabled: field.enabled
            cursorShape: Qt.IBeamCursor
        }
        background: Rectangle {
            radius: 6
            color: field.enabled ? "#292d30" : "#222629"
            border.width: 1
            border.color: field.activeFocus ? "#49bb80" : "#42494f"
        }
    }

    component StudioArea: TextArea {
        id: area
        // Grow naturally to fit long rules/flavor text. The left panel scrolls.
        property int minimumEditorHeight: 84
        Layout.minimumHeight: minimumEditorHeight
        Layout.preferredHeight: Math.max(
            minimumEditorHeight,
            area.contentHeight + area.topPadding + area.bottomPadding + 6
        )
        font.pixelSize: 13
        color: "#f2f4f5"
        placeholderTextColor: "#89919a"
        selectionColor: "#23784e"
        selectedTextColor: "white"
        wrapMode: TextEdit.Wrap
        leftPadding: 11
        rightPadding: 11
        topPadding: 11
        bottomPadding: 11
        HoverHandler {
            enabled: area.enabled
            cursorShape: Qt.IBeamCursor
        }
        background: Rectangle {
            radius: 6
            color: area.enabled ? "#292d30" : "#222629"
            border.width: 1
            border.color: area.activeFocus ? "#49bb80" : "#42494f"
        }
    }

    component StudioButton: Button {
        id: baseButton
        property bool primary: false
        property bool subtle: false
        font.pixelSize: primary ? 15 : 12
        font.bold: primary
        implicitHeight: primary ? 48 : 36
        // Don't show native disabled-hover artifacts on the primary action.
        hoverEnabled: enabled
        HoverHandler {
            enabled: baseButton.enabled
            cursorShape: Qt.PointingHandCursor
        }
        leftPadding: 12
        rightPadding: 12
        background: Rectangle {
            radius: 6
            color: !baseButton.enabled ? "#29312e"
                : baseButton.primary ? (baseButton.down ? "#176841" : baseButton.hovered ? "#239e61" : "#198754")
                : baseButton.subtle ? (baseButton.hovered ? "#333b40" : "#252b2f")
                : baseButton.hovered ? "#43494d" : "#343a3e"
            border.width: 1
            border.color: !baseButton.enabled ? "#3a4640"
                : baseButton.primary ? "#36af73" : "#4b5359"
        }
        contentItem: Text {
            text: baseButton.text
            font: baseButton.font
            color: baseButton.enabled ? "#f7fbf9" : "#818e87"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    FileDialog {
        id: artworkPicker
        title: "Choose card artwork"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)", "All files (*)"]
        onAccepted: workspace.manualArtworkUrl = selectedFile
    }
    Connections {
        target: studioCardModel
        function onChanged() {
            if (studioCardModel.loading) {
                // Avoid showing details from a different card during a new lookup.
                workspace.manualArtworkUrl = "";
                cardName.text = "";
                manaCost.text = "";
                typeLine.text = "";
                rulesText.text = "";
                flavorText.text = "";
                power.text = "";
                toughness.text = "";
                artist.text = "";
                setCode.text = "";
                rarity.text = "";
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

    Connections {
        target: studioRenderPreviewModel
        function onChanged() {
            const image = studioRenderPreviewModel.preview_url;
            if (!image) return;
            // Force Qt to reload exports that reuse the same filename.
            workspace.previewCardUrl = "";
            Qt.callLater(function() { workspace.previewCardUrl = image; });
        }
    }

    Connections {
        target: studioRenderModel
        function onChanged() {
            if (studioRenderModel.phase === "complete" && workspace.pendingRenderSignature) {
                // The bridge exposes a URL only for a verified Studio export.
                if (studioRenderModel.last_output_url.length > 0)
                    workspace.lastRenderedSignature = workspace.pendingRenderSignature;
                workspace.pendingRenderSignature = "";
            } else if (studioRenderModel.phase === "error") {
                workspace.pendingRenderSignature = "";
            }
        }
    }

    Rectangle { anchors.fill: parent; color: "#111416" }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // LEFT: Card editor
        Rectangle {
            Layout.preferredWidth: 346
            Layout.minimumWidth: 280
            Layout.fillHeight: true
            radius: 10
            color: "#1d2124"
            border.color: workspace.stroke

            ScrollView {
                id: editorScroll
                anchors.fill: parent
                anchors.margins: 18
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                ColumnLayout {
                    width: editorScroll.availableWidth
                    spacing: 9

                    Text { text: "Card Details"; font.pixelSize: 20; font.bold: true; color: "#f5f6f7" }
                    Text {
                        text: "Search, customize, and render a single card."
                        color: workspace.muted
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        Layout.bottomMargin: 10
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 7
                        StudioField {
                            id: cardSearchField
                            Layout.fillWidth: true
                            enabled: !studioCardModel.loading && !studioRenderModel.busy
                            placeholderText: "Search Scryfall..."
                            onAccepted: studioCardModel.lookup(text)
                        }
                        StudioButton {
                            text: studioCardModel.loading ? "Finding..." : "Find"
                            enabled: !studioCardModel.loading && !studioRenderModel.busy
                                && cardSearchField.text.trim().length > 0
                            onClicked: studioCardModel.lookup(cardSearchField.text)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: studioCardModel.loading || studioCardModel.error.length > 0
                        spacing: 8
                        BusyIndicator {
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            running: studioCardModel.loading
                            visible: running
                        }
                        Text {
                            Layout.fillWidth: true
                            text: studioCardModel.loading ? "Looking up card..." : studioCardModel.error
                            color: studioCardModel.error.length ? "#efaa9e" : "#cad2d8"
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 7
                        Layout.bottomMargin: 4
                        color: workspace.stroke
                    }
                    Text { text: "CARD INFORMATION"; color: workspace.muted; font.pixelSize: 11; font.bold: true; Layout.bottomMargin: 3 }

                    Text { text: "Name"; color: cardName.text.trim().length > 0 ? "#80c7a1" : "#d68b87"; font.pixelSize: 12 }
                    StudioField {
                        id: cardName
                        Layout.fillWidth: true
                        enabled: !studioRenderModel.busy
                        placeholderText: "Card name"
                    }
                    Text { text: "Mana cost"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioField {
                        id: manaCost
                        Layout.fillWidth: true
                        enabled: !studioRenderModel.busy
                        placeholderText: "{G}, {2}{U}, etc."
                    }
                    Text { text: "Type line"; color: typeLine.text.trim().length > 0 ? "#80c7a1" : "#d68b87"; font.pixelSize: 12 }
                    StudioField {
                        id: typeLine
                        Layout.fillWidth: true
                        enabled: !studioRenderModel.busy
                        placeholderText: "Creature — Elf Druid"
                    }
                    Text { text: "Rules text"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioArea {
                        id: rulesText
                        Layout.fillWidth: true
                        minimumEditorHeight: 104
                        enabled: !studioRenderModel.busy
                        placeholderText: "Card abilities..."
                    }
                    Text { text: "Flavor text"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioArea {
                        id: flavorText
                        Layout.fillWidth: true
                        minimumEditorHeight: 84
                        enabled: !studioRenderModel.busy
                        placeholderText: "Optional flavor text..."
                    }
                    Text { text: "Power / Toughness"; color: "#c4cbd0"; font.pixelSize: 12 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        StudioField {
                            id: power
                            Layout.fillWidth: true
                            enabled: !studioRenderModel.busy
                            placeholderText: "Power"
                        }
                        Text { text: "/"; color: workspace.muted; font.pixelSize: 18 }
                        StudioField {
                            id: toughness
                            Layout.fillWidth: true
                            enabled: !studioRenderModel.busy
                            placeholderText: "Toughness"
                        }
                    }
                    Text { text: "Artist"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioField {
                        id: artist
                        Layout.fillWidth: true
                        enabled: !studioRenderModel.busy
                        placeholderText: "Artist credit"
                    }
                    Text { text: "Set / Rarity"; color: "#c4cbd0"; font.pixelSize: 12 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        StudioField {
                            id: setCode
                            Layout.fillWidth: true
                            enabled: !studioRenderModel.busy
                            placeholderText: "Set code"
                        }
                        StudioField {
                            id: rarity
                            Layout.fillWidth: true
                            enabled: !studioRenderModel.busy
                            placeholderText: "common, rare..."
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 11
                        Layout.bottomMargin: 6
                        color: workspace.stroke
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Artwork"; color: "#f5f6f7"; font.pixelSize: 17; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            Layout.preferredWidth: sourceText.implicitWidth + 16
                            Layout.preferredHeight: 24
                            radius: 12
                            color: workspace.hasCustomArtwork ? "#223b30" : "#2b3439"
                            Text {
                                id: sourceText
                                anchors.centerIn: parent
                                text: workspace.effectiveArtworkUrl.toString().length === 0 ? "NO ART"
                                    : workspace.hasCustomArtwork ? "CUSTOM" : "SCRYFALL"
                                color: workspace.hasCustomArtwork ? "#8bd7a9" : "#bacbd5"
                                font.bold: true
                                font.pixelSize: 10
                            }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: workspace.effectiveArtworkUrl.toString().length ? 196 : 94
                        radius: 7
                        color: "#15191c"
                        border.color: workspace.stroke
                        clip: true
                        Image {
                            id: artworkPreview
                            anchors.fill: parent
                            anchors.margins: 8
                            source: workspace.effectiveArtworkUrl
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }
                        BusyIndicator {
                            anchors.centerIn: parent
                            running: artworkPreview.status === Image.Loading
                            visible: running
                        }
                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 28
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            color: workspace.muted
                            font.pixelSize: 12
                            visible: artworkPreview.status === Image.Null || artworkPreview.status === Image.Error
                            text: artworkPreview.status === Image.Error
                                ? "Artwork preview could not be loaded" : "Find a card or choose an image"
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: workspace.hasCustomArtwork ? "Using your selected image"
                            : "Scryfall artwork · " + (studioCardModel.card.artist || "Artist unknown")
                        visible: workspace.effectiveArtworkUrl.toString().length > 0
                        color: workspace.muted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        StudioButton {
                            text: workspace.hasCustomArtwork ? "Replace artwork..." : "Choose artwork..."
                            enabled: !studioRenderModel.busy && !studioCardModel.loading
                            onClicked: artworkPicker.open()
                        }
                        StudioButton {
                            text: "Use Scryfall"
                            subtle: true
                            visible: workspace.hasCustomArtwork && workspace.scryfallArtworkUrl.length > 0
                            enabled: !studioRenderModel.busy
                            onClicked: workspace.manualArtworkUrl = ""
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.topMargin: 9
                        text: "Edits affect the next Studio render. Projects are not saved yet."
                        color: "#79838b"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }

        // CENTER: Automatically refreshed PhotoCraft exports.
        Rectangle {
            Layout.fillWidth: true
            Layout.minimumWidth: 265
            Layout.fillHeight: true
            radius: 10
            color: "#1d2124"
            border.color: workspace.stroke

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 11

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 9

                    Text {
                        text: "Card Preview"
                        color: "#f5f6f7"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    // Compact output-folder action next to the title.
                    Button {
                        id: openOutputFolderButton
                        HoverHandler {
                            enabled: openOutputFolderButton.enabled
                            cursorShape: Qt.PointingHandCursor
                        }
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        implicitWidth: 32
                        implicitHeight: 32
                        hoverEnabled: true
                        ToolTip.visible: hovered
                        ToolTip.delay: 550
                        ToolTip.text: "Open output folder"
                        Accessible.name: "Open output folder"
                        onClicked: Qt.openUrlExternally(filePathModel.out_directory)

                        background: Rectangle {
                            radius: 6
                            color: openOutputFolderButton.down ? "#343d42"
                                : openOutputFolderButton.hovered ? "#30383d" : "#252b2f"
                            border.width: 1
                            border.color: openOutputFolderButton.activeFocus ? "#49bb80" : "#42494f"
                        }

                        contentItem: Item {
                            Canvas {
                                anchors.centerIn: parent
                                width: 20
                                height: 20
                                onPaint: {
                                const ctx = getContext("2d");
                                ctx.clearRect(0, 0, width, height);
                                ctx.lineWidth = 1.65;
                                ctx.strokeStyle = "#cdd4d8";
                                ctx.lineJoin = "round";
                                ctx.lineCap = "round";
                                ctx.beginPath();
                                ctx.moveTo(2.5, 6.5);
                                ctx.lineTo(2.5, 4.8);
                                ctx.lineTo(8, 4.8);
                                ctx.lineTo(10, 7);
                                ctx.lineTo(17.2, 7);
                                ctx.lineTo(17.2, 15.5);
                                ctx.lineTo(2.5, 15.5);
                                ctx.closePath();
                                ctx.stroke();
                                ctx.beginPath();
                                ctx.moveTo(2.5, 8.2);
                                ctx.lineTo(17.2, 8.2);
                                ctx.stroke();
                                }
                            }
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        Layout.preferredWidth: previewChipText.implicitWidth + 20
                        Layout.preferredHeight: 24
                        radius: 12
                        color: workspace.previewBadgeBackground
                        border.width: 1
                        border.color: workspace.previewBadgeText === "CURRENT PREVIEW" ? "#3d5b48"
                            : workspace.previewBadgeText === "NEEDS RENDER" ? "#5b4d37"
                            : "#3d474d"

                        Text {
                            id: previewChipText
                            anchors.centerIn: parent
                            color: workspace.previewBadgeForeground
                            font.pixelSize: 10
                            font.bold: true
                            text: workspace.previewBadgeText
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 230
                    radius: 8
                    color: "#141719"
                    border.color: "#32383d"
                    clip: true

                    Image {
                        id: renderedCardImage
                        anchors.fill: parent
                        anchors.margins: 15
                        source: workspace.previewCardUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                    }

                    BusyIndicator {
                        anchors.centerIn: parent
                        running: renderedCardImage.status === Image.Loading
                        visible: running
                    }

                    Column {
                        anchors.centerIn: parent
                        width: parent.width - 50
                        spacing: 9
                        visible: renderedCardImage.status === Image.Null || renderedCardImage.status === Image.Error
                        Text {
                            width: parent.width
                            text: renderedCardImage.status === Image.Error
                                ? "Preview unavailable"
                                : "Your rendered card will appear here"
                            font.pixelSize: 17
                            font.bold: true
                            color: "#c9d0d3"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            width: parent.width
                            text: renderedCardImage.status === Image.Error
                                ? "Check the output folder for the exported file."
                                : "Click Render Card to create a preview."
                            font.pixelSize: 12
                            color: workspace.muted
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        // RIGHT: Template selection and Studio-only render controls.
        Rectangle {
            Layout.preferredWidth: 310
            Layout.minimumWidth: 245
            Layout.fillHeight: true
            radius: 10
            color: "#1d2124"
            border.color: workspace.stroke

            ScrollView {
                id: renderSettingsScroll
                anchors.fill: parent
                anchors.margins: 18
                anchors.bottomMargin: 138
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                ColumnLayout {
                    width: renderSettingsScroll.availableWidth
                    spacing: 11
                    Text { text: "Render Settings"; color: "#f5f6f7"; font.pixelSize: 20; font.bold: true }
                    Text {
                        text: "Choose an installed frame for your card."
                        color: workspace.muted
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        Layout.bottomMargin: 12
                    }
                    Text { text: "Frame template"; color: "#c4cbd0"; font.pixelSize: 12 }
                    ComboBox {
                        id: templatePicker
                        HoverHandler {
                            enabled: templatePicker.enabled
                            cursorShape: Qt.PointingHandCursor
                        }
                        Layout.fillWidth: true
                        enabled: !studioRenderModel.busy
                        model: templateListModel
                        textRole: "name"
                        currentIndex: templateListModel.selected_index
                        onActivated: function(index) {
                            if (templateListModel.get_data(index, "is_installed"))
                                templateListModel.selected_index = index;
                            else
                                currentIndex = templateListModel.selected_index;
                        }
                        background: Rectangle {
                            radius: 6
                            color: "#292d30"
                            border.color: templatePicker.activeFocus ? "#49bb80" : "#42494f"
                        }
                        delegate: ItemDelegate {
                            id: templateOption
                            HoverHandler {
                                enabled: templateOption.enabled
                                cursorShape: Qt.PointingHandCursor
                            }
                            required property int index
                            required property string name
                            required property bool is_installed
                            width: templatePicker.width
                            text: name + (is_installed ? "" : " (not installed)")
                            enabled: is_installed
                            highlighted: templatePicker.highlightedIndex === index
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Rectangle {
                            Layout.preferredWidth: 7
                            Layout.preferredHeight: 7
                            radius: 4
                            color: workspace.selectedTemplateInstalled ? "#4acc82" : "#e4ab69"
                        }
                        Text {
                            text: workspace.selectedTemplateInstalled
                                ? "Installed and available" : "Template not installed"
                            color: workspace.selectedTemplateInstalled ? "#a7ddbd" : "#ecc99d"
                            font.pixelSize: 12
                            Layout.fillWidth: true
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 255
                        radius: 8
                        color: "#141719"
                        border.color: "#32383d"
                        Image {
                            id: templatePreviewImage
                            anchors.fill: parent
                            anchors.margins: 12
                            source: workspace.selectedTemplatePreviewUrl
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }
                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 25
                            text: "No template preview available"
                            color: workspace.muted
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            font.pixelSize: 12
                            visible: templatePreviewImage.status === Image.Null || templatePreviewImage.status === Image.Error
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: workspace.selectedTemplateName
                        color: "#f5f6f7"
                        font.pixelSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 9
                        Layout.bottomMargin: 7
                        color: workspace.stroke
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "The original Render button at the top remains available for batch and file-based workflows."
                        color: workspace.muted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // Persistent action area — stays visible while settings scroll.
            // One grouped status card replaces the scattered status/footer lines.
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 128
                radius: 10
                color: "#1d2124"

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 1
                    color: workspace.stroke
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    anchors.topMargin: 12
                    anchors.bottomMargin: 12
                    spacing: 10

                    StudioButton {
                        id: studioRenderButton
                        Layout.fillWidth: true
                        primary: true
                        enabled: workspace.canRender
                        text: studioRenderModel.busy ? "Working..." : "Render Card"
                        onClicked: workspace.sendRender()
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: 7

                        // One compact, low-saturation status label.
                        color: workspace.renderStatusTone === "error" ? "#342b2c"
                            : workspace.renderStatusTone === "working" ? "#2a3034"
                            : workspace.renderStatusTone === "attention" ? "#302e29"
                            : "#29332e"
                        border.width: 1
                        border.color: workspace.renderStatusTone === "error" ? "#62494c"
                            : workspace.renderStatusTone === "working" ? "#45525a"
                            : workspace.renderStatusTone === "attention" ? "#524b40"
                            : "#43584b"

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            text: workspace.renderStatusTitle
                            color: workspace.renderStatusTone === "error" ? "#dcb6b9"
                                : workspace.renderStatusTone === "working" ? "#bdcbd3"
                                : workspace.renderStatusTone === "attention" ? "#d6c7a6"
                                : "#afcdbc"
                            font.pixelSize: 12
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }
}
