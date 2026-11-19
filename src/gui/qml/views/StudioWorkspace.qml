import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    // The Studio workflow intentionally remains separate from the legacy Render button.
    property url previewCardUrl: ""
    property var dualPreviewUrls: ["", ""]

    // One independent draft per face; switching the editor/preview never
    // modifies the other face or makes a finished preview stale.
    property var faceDrafts: []
    property int activeFaceIndex: 0
    property bool loadingFaceFields: false
    readonly property bool isDualFace: studioCardModel.card.layout_kind === "transform"
        || studioCardModel.card.layout_kind === "mdfc"
    readonly property bool renderBusy: studioRenderModel.busy || studioDualRenderModel.busy
    readonly property var activeFaceDraft: faceDrafts.length > activeFaceIndex
        ? faceDrafts[activeFaceIndex] : ({})
    readonly property string manualArtworkUrl: activeFaceDraft.manual_artwork || ""

    function captureCurrentFace() {
        if (loadingFaceFields || faceDrafts.length <= activeFaceIndex)
            return;
        const drafts = faceDrafts.slice();
        const existing = drafts[activeFaceIndex];
        drafts[activeFaceIndex] = Object.assign({}, existing, {
            name: cardName.text,
            mana_cost: manaCost.text,
            type_line: typeLine.text,
            oracle_text: rulesText.text,
            flavor_text: flavorText.text,
            include_flavor_text: includeFlavorText ? "true" : "false",
            power: power.text,
            toughness: toughness.text,
            artist: artist.text,
            set: setCode.text,
            rarity: rarity.text
        });
        faceDrafts = drafts;
    }

    function selectFace(index) {
        if (index < 0 || index >= faceDrafts.length || renderBusy)
            return;
        captureCurrentFace();
        activeFaceIndex = index;
        loadingFaceFields = true;
        const face = faceDrafts[index];
        cardName.text = face.name || "";
        manaCost.text = face.mana_cost || "";
        typeLine.text = face.type_line || "";
        rulesText.text = face.oracle_text || "";
        flavorText.text = face.flavor_text || "";
        power.text = face.power || "";
        toughness.text = face.toughness || "";
        artist.text = face.artist || "";
        setCode.text = face.set || "";
        rarity.text = face.rarity || "";
        includeFlavorText = face.include_flavor_text !== "false";
        loadingFaceFields = false;
    }

    function setActiveArtwork(url) {
        if (renderBusy || faceDrafts.length <= activeFaceIndex)
            return;
        const drafts = faceDrafts.slice();
        drafts[activeFaceIndex] = Object.assign({}, drafts[activeFaceIndex], {
            manual_artwork: url.toString()
        });
        faceDrafts = drafts;
    }

    function initializeFaces() {
        loadingFaceFields = true;
        activeFaceIndex = 0;
        const card = studioCardModel.card;
        faceDrafts = (card.faces || []).map(function(f) {
            return Object.assign({}, f);
        });
        // Don't display a previous card's render as though it belonged to this lookup.
        previewCardUrl = "";
        dualPreviewUrls = ["", ""];
        lastRenderedSignature = "";
        lastPsdSignature = "";
        pendingRenderSignature = "";
        // A newly looked-up card has no matching exports for either face.
        lastRenderedFaceSignatures = ["", ""];
        lastPsdFaceSignatures = ["", ""];
        pendingFaceRenderSignatures = ["", ""];
        if (faceDrafts.length > 0)
            selectFace(0);  // loadingFaceFields prevents overwriting newly loaded data.
        loadingFaceFields = false;
    }

    // Save the exact form state submitted for the latest Studio render.
    // These are local UI snapshots, not an attempt to inspect the exported JPG.
    property string pendingRenderSignature: ""
    property string lastRenderedSignature: ""
    property string lastPsdSignature: ""
    // Two-sided previews must be tracked independently: editing one side
    // cannot invalidate the unchanged side's already-rendered preview.
    property var pendingFaceRenderSignatures: ["", ""]
    property var lastRenderedFaceSignatures: ["", ""]
    property var lastPsdFaceSignatures: ["", ""]

    // Template Options V1: keep Borderless selections during this Studio session.
    property string borderlessTextboxSize: "Automatic"
    property bool borderlessTextless: false
    property bool borderlessDropShadow: true
    property bool borderlessOptionsInitialized: false

    // Global Studio-only options. Scryfall flavor text stays editable even when
    // excluded from export. Manual edit saves a PSD, then launches PhotoCraft.
    property bool includeFlavorText: true
    property bool saveEditablePsd: false
    readonly property bool showBorderlessOptions:
        studioRenderModel.supports_borderless_options(selectedTemplateIndex)

    function loadBorderlessOptionsOnce() {
        if (!showBorderlessOptions || borderlessOptionsInitialized)
            return;
        const defaults = studioRenderModel.borderless_defaults(selectedTemplateIndex);
        borderlessTextboxSize = defaults.textbox_size || "Automatic";
        borderlessTextless = Boolean(defaults.textless);
        borderlessDropShadow = Boolean(defaults.drop_shadow);
        borderlessOptionsInitialized = true;
    }
    onSelectedTemplateIndexChanged: loadBorderlessOptionsOnce()
    Component.onCompleted: loadBorderlessOptionsOnce()

    readonly property string currentEditorSignature: JSON.stringify([
        studioCardModel.card.name || "",
        studioCardModel.card.layout_kind || "",
        faceDrafts,
        saveEditablePsd,
        selectedTemplateName,
        selectedTemplateIndex >= 0
            ? (templateListModel.get_data(selectedTemplateIndex, "plugin_id") || "")
            : "",
        showBorderlessOptions ? borderlessTextboxSize : "",
        showBorderlessOptions ? borderlessTextless : false,
        showBorderlessOptions ? borderlessDropShadow : false
    ])

    // This signature contains only the selected face's editable data plus
    // settings shared by both faces. Template changes still stale BOTH sides.
    function faceRenderSignature(index, drafts) {
        const face = drafts[index] || {};
        return JSON.stringify([
            studioCardModel.card.name || "",
            studioCardModel.card.layout_kind || "",
            face,
            saveEditablePsd,
            selectedTemplateName,
            selectedTemplateIndex >= 0
                ? (templateListModel.get_data(selectedTemplateIndex, "plugin_id") || "")
                : "",
            showBorderlessOptions ? borderlessTextboxSize : "",
            showBorderlessOptions ? borderlessTextless : false,
            showBorderlessOptions ? borderlessDropShadow : false
        ]);
    }
    readonly property string currentFaceSignature: isDualFace
        ? faceRenderSignature(activeFaceIndex, faceDrafts) : currentEditorSignature
    readonly property string frontRenderedUrl: dualPreviewUrls.length > 0 ? dualPreviewUrls[0] : ""
    readonly property string backRenderedUrl: dualPreviewUrls.length > 1 ? dualPreviewUrls[1] : ""
    readonly property string displayedPreviewUrl: isDualFace
        ? (activeFaceIndex === 0 ? frontRenderedUrl : backRenderedUrl)
        : previewCardUrl.toString()
    readonly property string activePhase: isDualFace ? studioDualRenderModel.phase : studioRenderModel.phase
    readonly property string activeStatus: isDualFace ? studioDualRenderModel.status : studioRenderModel.status
    readonly property string activeLaunchWarning: isDualFace
        ? studioDualRenderModel.launch_warning : studioRenderModel.launch_warning
    readonly property string activeLastOutput: isDualFace
        ? studioDualRenderModel.last_output_url : studioRenderModel.last_output_url

    // The queue reports whether this specific preview came from Studio.
    // Compare that provenance and the submitted form snapshot instead of
    // comparing URL strings (which Qt may normalize differently).
    readonly property bool currentPsdSaved: isDualFace
        ? lastPsdFaceSignatures.length > activeFaceIndex
            && lastPsdFaceSignatures[activeFaceIndex].length > 0
            && lastPsdFaceSignatures[activeFaceIndex] === currentFaceSignature
            && (activeFaceIndex === 0
                ? studioDualRenderModel.front_output_url
                : studioDualRenderModel.back_output_url).toLowerCase().endsWith(".psd")
        : lastPsdSignature.length > 0
            && lastPsdSignature === currentEditorSignature
            && activeLastOutput.toLowerCase().endsWith(".psd")

    readonly property bool previewIsCurrent: isDualFace
        ? lastRenderedFaceSignatures.length > activeFaceIndex
            && lastRenderedFaceSignatures[activeFaceIndex].length > 0
            && lastRenderedFaceSignatures[activeFaceIndex] === currentFaceSignature
            && displayedPreviewUrl.length > 0
        : lastRenderedSignature.length > 0
            && lastRenderedSignature === currentEditorSignature
            && renderedCardImage.status === Image.Ready
            && studioRenderPreviewModel.preview_is_studio

    readonly property string previewBadgeText:
        renderBusy ? "RENDERING"
        : currentPsdSaved ? "PSD EXPORTED"
        : displayedPreviewUrl.length === 0 ? "NO PREVIEW"
        : previewIsCurrent ? "CURRENT PREVIEW" : "NEEDS RENDER"

    readonly property string previewBadgeBackground:
        previewBadgeText === "CURRENT PREVIEW" || previewBadgeText === "PSD EXPORTED" ? "#26372f"
        : previewBadgeText === "NEEDS RENDER" ? "#373127"
        : previewBadgeText === "RENDERING" ? "#2c353c" : "#30363b"

    readonly property string previewBadgeForeground:
        previewBadgeText === "CURRENT PREVIEW" || previewBadgeText === "PSD EXPORTED" ? "#b4d8c3"
        : previewBadgeText === "NEEDS RENDER" ? "#dec8a2"
        : previewBadgeText === "RENDERING" ? "#b7cdd9" : "#aab3bb"

    readonly property string scryfallArtworkUrl: activeFaceDraft.art_crop || ""
    readonly property bool hasCustomArtwork: manualArtworkUrl.length > 0
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
    readonly property bool selectedTemplateSupportsCard: !isDualFace
        || studioDualRenderModel.supports_layout(selectedTemplateIndex, studioCardModel.card.layout_kind || "")
    readonly property string missingRequirement: {
        if (studioCardModel.loading) return "Looking up card details...";
        if (!studioCardModel.card.layout_kind) return "Find a card or create a new one.";
        if (studioCardModel.card.studio_compatible === "no")
            return "Use the original Render button for this special layout.";
        if (faceDrafts.length !== (isDualFace ? 2 : 1))
            return "Loading card faces...";
        for (let i = 0; i < faceDrafts.length; i++) {
            const face = faceDrafts[i];
            const side = isDualFace ? (i === 0 ? "front" : "back") + " face" : "card";
            if (!(face.name || "").trim()) return "Enter a name for the " + side + ".";
            if (!(face.type_line || "").trim()) return "Enter a type line for the " + side + ".";
            if (!(face.manual_artwork || face.art_crop || "").length)
                return "Choose artwork for the " + side + ".";
        }
        if (isDualFace && faceDrafts[0].name.trim().toLowerCase() === faceDrafts[1].name.trim().toLowerCase())
            return "The two faces need different names.";
        if (!selectedTemplateInstalled) return "Select an installed template.";
        if (!selectedTemplateSupportsCard)
            return "Choose a template that supports both faces.";
        return "";
    }
    readonly property bool canRender: !renderBusy && missingRequirement.length === 0

    // A missing field takes priority over stale errors from a previous render.
    readonly property string renderStatusTone:
        renderBusy ? "working"
        : missingRequirement.length > 0 ? "attention"
        : activePhase === "error" ? "error"
        : "success"

    readonly property string renderStatusTitle:
        renderBusy ? (activeStatus || "Rendering in PhotoCraft...")
        : missingRequirement.length > 0 ? "Not ready to render"
        : activePhase === "error" ? "Render failed"
        : activePhase === "complete" && currentPsdSaved
            ? (activeLaunchWarning.length > 0
                ? "PSD saved · open manually"
                : activeStatus.indexOf("PhotoCraft") >= 0
                    ? "Opened in PhotoCraft" : "PSD saved")
        : activePhase === "complete" && previewIsCurrent ? "Render complete"
        : "Ready to render"

    // ProxyStudio: show the exact missing requirement below the render status.
    readonly property string renderStatusDetail: !renderBusy && missingRequirement.length > 0
        ? missingRequirement : ""

    readonly property color accent: "#44bf7e"
    readonly property color muted: "#9da5ae"
    readonly property color stroke: "#373e43"

    function sendRender() {
        if (!canRender) return;
        captureCurrentFace();
        if (isDualFace) {
            // Snapshot BOTH faces at submission, not at completion. Later
            // edits must not be incorrectly marked as already rendered.
            pendingFaceRenderSignatures = [
                faceRenderSignature(0, faceDrafts),
                faceRenderSignature(1, faceDrafts)
            ];
            pendingRenderSignature = "";
        } else {
            pendingRenderSignature = currentEditorSignature;
            pendingFaceRenderSignatures = ["", ""];
        }
        const shared = {
            editable_psd: saveEditablePsd ? "true" : "false",
            template_textbox_size: borderlessTextboxSize,
            template_textless: borderlessTextless ? "true" : "false",
            template_drop_shadow: borderlessDropShadow ? "true" : "false"
        };
        if (isDualFace) {
            studioDualRenderModel.render_card(Object.assign({}, shared, {faces: faceDrafts}));
        } else {
            studioRenderModel.render_card(Object.assign({}, shared, faceDrafts[0]));
        }
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
        onAccepted: workspace.setActiveArtwork(selectedFile)
    }
    Connections {
        target: studioCardModel
        function onChanged() {
            if (studioCardModel.loading) {
                workspace.loadingFaceFields = true;
                workspace.faceDrafts = [];
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
                workspace.loadingFaceFields = false;
                return;
            }
            if (studioCardModel.card.layout_kind)
                workspace.initializeFaces();
        }
    }

    Connections {
        target: studioRenderPreviewModel
        function onChanged() {
            const image = studioRenderPreviewModel.preview_url;
            if (!image || workspace.isDualFace) return;
            // Force Qt to reload exports that reuse the same filename.
            workspace.previewCardUrl = "";
            Qt.callLater(function() { workspace.previewCardUrl = image; });
        }
    }

    Connections {
        target: studioRenderModel
        function onChanged() {
            if (studioRenderModel.phase === "complete" && workspace.pendingRenderSignature) {
                const url = studioRenderModel.last_output_url.toLowerCase();
                if (url.endsWith(".psd")) {
                    // A PSD is not a viewable bitmap. Show a clear export-success state.
                    workspace.lastPsdSignature = workspace.pendingRenderSignature;
                    workspace.lastRenderedSignature = "";
                    workspace.previewCardUrl = "";
                } else if (url.length > 0) {
                    workspace.lastRenderedSignature = workspace.pendingRenderSignature;
                    workspace.lastPsdSignature = "";
                }
                workspace.pendingRenderSignature = "";
            } else if (studioRenderModel.phase === "error") {
                workspace.pendingRenderSignature = "";
            }
        }
    }

    Connections {
        target: studioDualRenderModel
        function onChanged() {
            if (studioDualRenderModel.phase === "complete" && workspace.isDualFace
                    && workspace.pendingFaceRenderSignatures.length === 2
                    && workspace.pendingFaceRenderSignatures[0].length > 0) {
                const front = studioDualRenderModel.front_output_url;
                const back = studioDualRenderModel.back_output_url;
                if (front.toLowerCase().endsWith(".psd") && back.toLowerCase().endsWith(".psd")) {
                    workspace.lastPsdFaceSignatures = workspace.pendingFaceRenderSignatures.slice();
                    workspace.lastRenderedFaceSignatures = ["", ""];
                    workspace.dualPreviewUrls = ["", ""];
                } else if (front.length > 0 && back.length > 0) {
                    workspace.lastRenderedFaceSignatures = workspace.pendingFaceRenderSignatures.slice();
                    workspace.lastPsdFaceSignatures = ["", ""];
                    workspace.dualPreviewUrls = ["", ""];
                    Qt.callLater(function() { workspace.dualPreviewUrls = [front, back]; });
                }
                workspace.pendingFaceRenderSignatures = ["", ""];
            } else if (studioDualRenderModel.phase === "error") {
                workspace.pendingFaceRenderSignatures = ["", ""];
            }
        }
    }

    // A small creation menu; the existing Studio form handles all layouts.
    Popup {
        id: createCardPopup
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: 318
        padding: 17
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle {
            radius: 10
            color: "#22282c"
            border.color: "#506459"
            border.width: 1
        }
        ColumnLayout {
            width: parent.width
            spacing: 10
            Text {
                text: "Create Card"
                color: "#f5f7f6"
                font.bold: true
                font.pixelSize: 19
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Choose a layout. Start with blank fields and add your own artwork."
                color: workspace.muted
                font.pixelSize: 12
                Layout.bottomMargin: 6
            }
            StudioButton {
                Layout.fillWidth: true
                text: "Normal  ·  Single face"
                onClicked: {
                    studioCardModel.create_card("normal");
                    cardSearchField.text = "";
                    createCardPopup.close();
                }
            }
            StudioButton {
                Layout.fillWidth: true
                text: "Transform  ·  Front + back"
                onClicked: {
                    studioCardModel.create_card("transform");
                    cardSearchField.text = "";
                    createCardPopup.close();
                }
            }
            StudioButton {
                Layout.fillWidth: true
                text: "Modal DFC  ·  Front + back"
                onClicked: {
                    studioCardModel.create_card("mdfc");
                    cardSearchField.text = "";
                    createCardPopup.close();
                }
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
                        text: "Find an existing card or create one from scratch."
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
                            enabled: !studioCardModel.loading && !workspace.renderBusy
                            placeholderText: "Search Scryfall..."
                            onAccepted: studioCardModel.lookup(text)
                        }
                        StudioButton {
                            text: studioCardModel.loading ? "Finding..." : "Find"
                            enabled: !studioCardModel.loading && !workspace.renderBusy
                                && cardSearchField.text.trim().length > 0
                            onClicked: studioCardModel.lookup(cardSearchField.text)
                        }
                    }
                    StudioButton {
                        Layout.fillWidth: true
                        subtle: true
                        text: "+ Create Card"
                        enabled: !studioCardModel.loading && !workspace.renderBusy
                        onClicked: createCardPopup.open()
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        visible: workspace.isDualFace
                        spacing: 7
                        Text {
                            text: studioCardModel.card.layout_kind === "mdfc" ? "MODAL DFC" : "TRANSFORM"
                            color: "#9da5ae"
                            font.pixelSize: 10
                            font.bold: true
                            Layout.rightMargin: 5
                        }
                        Repeater {
                            model: ["Front", "Back"]
                            delegate: Button {
                                id: faceEditorTab
                                required property int index
                                required property string modelData
                                Layout.fillWidth: true
                                implicitHeight: 32
                                enabled: !workspace.renderBusy
                                text: modelData
                                hoverEnabled: enabled
                                HoverHandler {
                                    enabled: faceEditorTab.enabled
                                    cursorShape: Qt.PointingHandCursor
                                }
                                onClicked: workspace.selectFace(index)
                                background: Rectangle {
                                    radius: 6
                                    color: workspace.activeFaceIndex === index ? "#2a473a"
                                        : faceEditorTab.hovered ? "#343c40" : "#292e32"
                                    border.color: workspace.activeFaceIndex === index ? "#4d9e76" : workspace.stroke
                                    border.width: 1
                                }
                                contentItem: Text {
                                    text: faceEditorTab.text
                                    color: workspace.activeFaceIndex === index ? "#c6e8d4" : "#c8d0d5"
                                    font.pixelSize: 12
                                    font.bold: workspace.activeFaceIndex === index
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: workspace.isDualFace
                        text: "Each face has its own text and artwork. Both render together."
                        color: workspace.muted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.bottomMargin: 2
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
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        enabled: !workspace.renderBusy
                        placeholderText: "Card name"
                    }
                    Text { text: "Mana cost"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioField {
                        id: manaCost
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        enabled: !workspace.renderBusy
                        placeholderText: "{G}, {2}{U}, etc."
                    }
                    Text { text: "Type line"; color: typeLine.text.trim().length > 0 ? "#80c7a1" : "#d68b87"; font.pixelSize: 12 }
                    StudioField {
                        id: typeLine
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        enabled: !workspace.renderBusy
                        placeholderText: "Creature — Elf Druid"
                    }
                    Text { text: "Rules text"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioArea {
                        id: rulesText
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        minimumEditorHeight: 104
                        enabled: !workspace.renderBusy
                        placeholderText: "Card abilities..."
                    }
                    Text { text: "Flavor text"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioArea {
                        id: flavorText
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        minimumEditorHeight: 84
                        // Keep the Scryfall text editable even while exclusion is enabled.
                        enabled: !workspace.renderBusy
                        placeholderText: "Optional flavor text..."
                    }
                    Text { text: "Power / Toughness"; color: "#c4cbd0"; font.pixelSize: 12 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        StudioField {
                            id: power
                            onTextChanged: workspace.captureCurrentFace()
                            Layout.fillWidth: true
                            enabled: !workspace.renderBusy
                            placeholderText: "Power"
                        }
                        Text { text: "/"; color: workspace.muted; font.pixelSize: 18 }
                        StudioField {
                            id: toughness
                            onTextChanged: workspace.captureCurrentFace()
                            Layout.fillWidth: true
                            enabled: !workspace.renderBusy
                            placeholderText: "Toughness"
                        }
                    }
                    Text { text: "Artist"; color: "#c4cbd0"; font.pixelSize: 12 }
                    StudioField {
                        id: artist
                        onTextChanged: workspace.captureCurrentFace()
                        Layout.fillWidth: true
                        enabled: !workspace.renderBusy
                        placeholderText: "Artist credit"
                    }
                    Text { text: "Set / Rarity"; color: "#c4cbd0"; font.pixelSize: 12 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        StudioField {
                            id: setCode
                            onTextChanged: workspace.captureCurrentFace()
                            Layout.fillWidth: true
                            enabled: !workspace.renderBusy
                            placeholderText: "Set code"
                        }
                        StudioField {
                            id: rarity
                            onTextChanged: workspace.captureCurrentFace()
                            Layout.fillWidth: true
                            enabled: !workspace.renderBusy
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
                                ? "Artwork preview could not be loaded"
                                : studioCardModel.card.is_custom ? "Choose artwork for this face"
                                : "Find a card or choose an image"
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: workspace.hasCustomArtwork ? "Using your selected image"
                            : "Scryfall artwork · " + (workspace.activeFaceDraft.artist || "Artist unknown")
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
                            enabled: !workspace.renderBusy && !studioCardModel.loading
                            onClicked: artworkPicker.open()
                        }
                        StudioButton {
                            text: "Use Scryfall"
                            subtle: true
                            visible: workspace.hasCustomArtwork && workspace.scryfallArtworkUrl.length > 0
                            enabled: !workspace.renderBusy
                            onClicked: workspace.setActiveArtwork("")
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

                    RowLayout {
                        visible: workspace.isDualFace
                        spacing: 4
                        Repeater {
                            model: ["Front", "Back"]
                            delegate: Button {
                                id: previewFaceTab
                                required property int index
                                required property string modelData
                                text: modelData
                                implicitWidth: 58
                                implicitHeight: 30
                                enabled: !workspace.renderBusy
                                hoverEnabled: enabled
                                HoverHandler {
                                    enabled: previewFaceTab.enabled
                                    cursorShape: Qt.PointingHandCursor
                                }
                                onClicked: workspace.selectFace(index)
                                background: Rectangle {
                                    radius: 5
                                    color: workspace.activeFaceIndex === index ? "#2a473a"
                                        : previewFaceTab.hovered ? "#353b3f" : "#292e32"
                                    border.color: workspace.activeFaceIndex === index ? "#4d9e76" : workspace.stroke
                                    border.width: 1
                                }
                                contentItem: Text {
                                    text: previewFaceTab.text
                                    font.pixelSize: 11
                                    font.bold: workspace.activeFaceIndex === index
                                    color: workspace.activeFaceIndex === index ? "#c6e8d4" : "#c8d0d5"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
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
                        border.color: workspace.previewBadgeText === "CURRENT PREVIEW" || workspace.previewBadgeText === "PSD EXPORTED" ? "#3d5b48"
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
                        source: workspace.displayedPreviewUrl
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
                                : workspace.currentPsdSaved ? (workspace.isDualFace ? "Both editable PSDs saved" : "Editable PSD saved")
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
                                : workspace.currentPsdSaved
                                    ? (workspace.isDualFace
                                        ? "Both layered PSDs were saved. PhotoCraft opens them automatically when available."
                                        : "The layered PSD was saved. PhotoCraft opens automatically when available.")
                                    : workspace.isDualFace ? "Render both faces to preview either side."
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
                anchors.bottomMargin: workspace.renderStatusDetail.length > 0 ? 176 : 138
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                ColumnLayout {
                    width: renderSettingsScroll.availableWidth
                    spacing: 11
                    Text { text: "Render Settings"; color: "#f5f6f7"; font.pixelSize: 20; font.bold: true }
                    Text {
                        text: workspace.isDualFace ? "Choose a frame supporting both faces." : "Choose an installed frame for your card."
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
                        enabled: !workspace.renderBusy
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
                    Text {
                        Layout.fillWidth: true
                        visible: workspace.isDualFace && workspace.selectedTemplateInstalled
                            && !workspace.selectedTemplateSupportsCard
                        text: "This template does not support both card faces. Choose a double-faced template."
                        color: "#d6c7a6"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
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
                    // Template-specific options appear only when the selected
                    // normal-card template actually uses BorderlessVectorTemplate.
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: workspace.showBorderlessOptions
                        spacing: 11

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            Layout.topMargin: 8
                            Layout.bottomMargin: 6
                            color: workspace.stroke
                        }
                        Text {
                            text: "TEMPLATE OPTIONS"
                            font.pixelSize: 11
                            font.bold: true
                            color: "#a8b5bd"
                        }
                        Text {
                            text: "Textbox size"
                            color: "#c4cbd0"
                            font.pixelSize: 12
                        }
                        ComboBox {
                            id: borderlessSizePicker
                            Layout.fillWidth: true
                            enabled: !workspace.renderBusy && !workspace.borderlessTextless
                            model: ["Automatic", "Short", "Medium", "Normal", "Tall"]
                            currentIndex: model.indexOf(workspace.borderlessTextboxSize)
                            onActivated: function(index) {
                                workspace.borderlessTextboxSize = model[index];
                            }
                            HoverHandler {
                                enabled: borderlessSizePicker.enabled
                                cursorShape: Qt.PointingHandCursor
                            }
                            background: Rectangle {
                                radius: 6
                                color: borderlessSizePicker.enabled ? "#292d30" : "#222729"
                                border.color: borderlessSizePicker.activeFocus ? "#49bb80" : "#42494f"
                            }
                            delegate: ItemDelegate {
                                id: sizeOption
                                required property string modelData
                                required property int index
                                width: borderlessSizePicker.width
                                text: modelData
                                highlighted: borderlessSizePicker.highlightedIndex === index
                                HoverHandler {
                                    enabled: sizeOption.enabled
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: workspace.borderlessTextless
                            text: "Textbox size is ignored in Textless mode."
                            color: workspace.muted
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: "Textless mode"
                                color: "#c4cbd0"
                                font.pixelSize: 12
                                Layout.fillWidth: true
                            }
                            Switch {
                                id: borderlessTextlessSwitch
                                text: ""
                                enabled: !workspace.renderBusy
                                checked: workspace.borderlessTextless
                                onToggled: workspace.borderlessTextless = checked
                                HoverHandler {
                                    enabled: borderlessTextlessSwitch.enabled
                                    cursorShape: Qt.PointingHandCursor
                                }
                                indicator: Rectangle {
                                    implicitWidth: 38
                                    implicitHeight: 22
                                    x: borderlessTextlessSwitch.leftPadding
                                    y: (parent.height - height) / 2
                                    radius: 11
                                    color: borderlessTextlessSwitch.checked ? "#28794f" : "#42494f"
                                    border.color: borderlessTextlessSwitch.checked ? "#4aad7a" : "#606a70"
                                    Rectangle {
                                        x: borderlessTextlessSwitch.checked ? parent.width - width - 3 : 3
                                        y: 3
                                        width: 16
                                        height: 16
                                        radius: 8
                                        color: "#f2f4f5"
                                    }
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: "Text drop shadow"
                                color: "#c4cbd0"
                                font.pixelSize: 12
                                Layout.fillWidth: true
                            }
                            Switch {
                                id: borderlessShadowSwitch
                                text: ""
                                enabled: !workspace.renderBusy
                                checked: workspace.borderlessDropShadow
                                onToggled: workspace.borderlessDropShadow = checked
                                HoverHandler {
                                    enabled: borderlessShadowSwitch.enabled
                                    cursorShape: Qt.PointingHandCursor
                                }
                                indicator: Rectangle {
                                    implicitWidth: 38
                                    implicitHeight: 22
                                    x: borderlessShadowSwitch.leftPadding
                                    y: (parent.height - height) / 2
                                    radius: 11
                                    color: borderlessShadowSwitch.checked ? "#28794f" : "#42494f"
                                    border.color: borderlessShadowSwitch.checked ? "#4aad7a" : "#606a70"
                                    Rectangle {
                                        x: borderlessShadowSwitch.checked ? parent.width - width - 3 : 3
                                        y: 3
                                        width: 16
                                        height: 16
                                        radius: 8
                                        color: "#f2f4f5"
                                    }
                                }
                            }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        Layout.topMargin: 9
                        Layout.bottomMargin: 7
                        color: workspace.stroke
                    }
                    Text {
                        text: "OUTPUT"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#a8b5bd"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Text {
                            text: "Include flavor text"
                            color: "#c4cbd0"
                            font.pixelSize: 12
                            Layout.fillWidth: true
                        }
                        Switch {
                            id: includeFlavorSwitch
                            text: ""
                            implicitHeight: 23
                            enabled: !workspace.renderBusy
                            checked: workspace.includeFlavorText
                            onToggled: {
                                workspace.includeFlavorText = checked;
                                workspace.captureCurrentFace();
                            }
                            HoverHandler {
                                enabled: includeFlavorSwitch.enabled
                                cursorShape: Qt.PointingHandCursor
                            }
                            indicator: Rectangle {
                                implicitWidth: 38
                                implicitHeight: 22
                                x: includeFlavorSwitch.leftPadding
                                y: (parent.height - height) / 2
                                radius: 11
                                color: includeFlavorSwitch.checked ? "#28794f" : "#42494f"
                                border.color: includeFlavorSwitch.checked ? "#4aad7a" : "#606a70"
                                Rectangle {
                                    x: includeFlavorSwitch.checked ? parent.width - width - 3 : 3
                                    y: 3
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "#f2f4f5"
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Text { text: "Manual edit in PhotoCraft"; color: "#c4cbd0"; font.pixelSize: 12 }
                            Text {
                                Layout.fillWidth: true
                                text: "Save a layered PSD and open it automatically"
                                color: workspace.muted
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Switch {
                            id: editablePsdSwitch
                            text: ""
                            enabled: !workspace.renderBusy
                            checked: workspace.saveEditablePsd
                            onToggled: workspace.saveEditablePsd = checked
                            HoverHandler {
                                enabled: editablePsdSwitch.enabled
                                cursorShape: Qt.PointingHandCursor
                            }
                            indicator: Rectangle {
                                implicitWidth: 38
                                implicitHeight: 22
                                x: editablePsdSwitch.leftPadding
                                y: (parent.height - height) / 2
                                radius: 11
                                color: editablePsdSwitch.checked ? "#28794f" : "#42494f"
                                border.color: editablePsdSwitch.checked ? "#4aad7a" : "#606a70"
                                Rectangle {
                                    x: editablePsdSwitch.checked ? parent.width - width - 3 : 3
                                    y: 3
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "#f2f4f5"
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: workspace.saveEditablePsd
                        text: "The PSD stays in your output folder. Use Save As in PhotoCraft for .pcraft or other formats."
                        color: workspace.muted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: workspace.activeLaunchWarning.length > 0
                        text: workspace.activeLaunchWarning
                        color: "#d6c7a6"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; Layout.topMargin: 7; Layout.bottomMargin: 4; color: workspace.stroke }
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
                height: workspace.renderStatusDetail.length > 0 ? 166 : 128
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
                        text: workspace.renderBusy ? "Working..."
                            : workspace.isDualFace ? (workspace.saveEditablePsd ? "Render & Edit Both" : "Render Both Faces")
                            : workspace.saveEditablePsd ? "Render & Edit" : "Render Card"
                        onClicked: workspace.sendRender()
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: workspace.renderStatusDetail.length > 0 ? 78 : 40
                        radius: 7

                        // The readiness explanation appears only when rendering is blocked.
                        color: workspace.renderStatusTone === "error" ? "#342b2c"
                            : workspace.renderStatusTone === "working" ? "#2a3034"
                            : workspace.renderStatusTone === "attention" ? "#302e29"
                            : "#29332e"
                        border.width: 1
                        border.color: workspace.renderStatusTone === "error" ? "#62494c"
                            : workspace.renderStatusTone === "working" ? "#45525a"
                            : workspace.renderStatusTone === "attention" ? "#524b40"
                            : "#43584b"

                        Column {
                            anchors.centerIn: parent
                            width: parent.width - 24
                            spacing: workspace.renderStatusDetail.length > 0 ? 4 : 0

                            Text {
                                width: parent.width
                                text: workspace.renderStatusTitle
                                color: workspace.renderStatusTone === "error" ? "#dcb6b9"
                                    : workspace.renderStatusTone === "working" ? "#bdcbd3"
                                    : workspace.renderStatusTone === "attention" ? "#d6c7a6"
                                    : "#afcdbc"
                                font.pixelSize: 12
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                            Text {
                                width: parent.width
                                visible: workspace.renderStatusDetail.length > 0
                                text: workspace.renderStatusDetail
                                color: "#c8c4ba"
                                font.pixelSize: 11
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }
    }
}
