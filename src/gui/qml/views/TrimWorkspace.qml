// Post-render bleed removal and rounded-corner PNG export.
// Independent of Studio and the original Proxyshop rendering workflow.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: workspace

    property bool showOriginal: false
    readonly property color textPrimary: "#f0f2f2"
    readonly property color textMuted: "#9fa9b1"
    readonly property color accent: "#50bd87"
    readonly property color borderColor: "#353c42"

    component TrimButton: Button {
        id: control
        property bool primary: false
        implicitHeight: 42
        leftPadding: 14
        rightPadding: 14
        font.pixelSize: 13
        font.bold: primary
        hoverEnabled: enabled
        contentItem: Text {
            text: control.text
            font: control.font
            color: control.enabled ? (control.primary ? "#0a2015" : "#e0e7e8") : "#818c90"
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
        HoverHandler {
            enabled: control.enabled
            cursorShape: Qt.PointingHandCursor
        }
        background: Rectangle {
            radius: 7
            color: !control.enabled ? "#29302d"
                : control.primary ? (control.down ? "#3d9e6d" : control.hovered ? "#60cd98" : "#50bd87")
                : control.down ? "#343c42" : control.hovered ? "#343c42" : "#292e33"
            border.color: control.primary && control.enabled ? "#419d6e" : "#414a50"
        }
    }

    FileDialog {
        id: sourcePicker
        title: "Open a card render"
        fileMode: FileDialog.OpenFile
        currentFolder: filePathModel.out_directory
        nameFilters: [
            "Card images (*.png *.jpg *.jpeg *.webp)",
            "All files (*)"
        ]
        onAccepted: {
            workspace.showOriginal = false;
            trimModel.open_image(selectedFile.toString());
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

        // Controls and source information
        Rectangle {
            Layout.preferredWidth: 315
            Layout.minimumWidth: 270
            Layout.fillHeight: true
            color: "#1b1e22"
            radius: 10
            border.color: workspace.borderColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 12

                Text {
                    text: "Trim"
                    color: workspace.textPrimary
                    font.bold: true
                    font.pixelSize: 21
                }

                Text {
                    Layout.fillWidth: true
                    text: "Remove print bleed and round the corners of a completed card render."
                    color: workspace.textMuted
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    lineHeight: 1.3
                }

                TrimButton {
                    Layout.fillWidth: true
                    Layout.topMargin: 10
                    text: "Open Rendered Card..."
                    enabled: !trimModel.busy
                    onClicked: sourcePicker.open()
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.topMargin: 6
                    Layout.bottomMargin: 4
                    color: workspace.borderColor
                }

                Text {
                    text: "SOURCE FILE"
                    font.bold: true
                    font.pixelSize: 11
                    font.letterSpacing: 0.6
                    color: workspace.textMuted
                }

                Text {
                    Layout.fillWidth: true
                    text: trimModel.source_name || "No card selected"
                    color: trimModel.source_name ? workspace.textPrimary : workspace.textMuted
                    font.pixelSize: 14
                    wrapMode: Text.WrapAnywhere
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 11

                    Text { text: "Original"; color: workspace.textMuted; font.pixelSize: 12 }
                    Text {
                        Layout.fillWidth: true
                        text: trimModel.original_dimensions || "—"
                        color: workspace.textPrimary
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                    Text { text: "Bleed removed"; color: workspace.textMuted; font.pixelSize: 12 }
                    Text {
                        Layout.fillWidth: true
                        text: "0.125\" per edge"
                        color: workspace.textPrimary
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                    Text { text: "Final size"; color: workspace.textMuted; font.pixelSize: 12 }
                    Text {
                        Layout.fillWidth: true
                        text: trimModel.output_dimensions || "—"
                        color: workspace.textPrimary
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                    Text { text: "Corners"; color: workspace.textMuted; font.pixelSize: 12 }
                    Text {
                        Layout.fillWidth: true
                        text: "Rounded / transparent"
                        color: workspace.textPrimary
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.topMargin: 7
                    Layout.bottomMargin: 4
                    color: workspace.borderColor
                }

                Text {
                    text: "OUTPUT"
                    font.bold: true
                    font.pixelSize: 11
                    font.letterSpacing: 0.6
                    color: workspace.textMuted
                }

                Text {
                    Layout.fillWidth: true
                    text: trimModel.can_save ? trimModel.output_name : "Original name + _trim.png"
                    color: workspace.textPrimary
                    font.pixelSize: 14
                    wrapMode: Text.WrapAnywhere
                }

                Text {
                    Layout.fillWidth: true
                    text: "The PNG saves beside your original image. The source file is never overwritten."
                    color: workspace.textMuted
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }

                Item { Layout.fillHeight: true }

                TrimButton {
                    Layout.fillWidth: true
                    primary: true
                    text: trimModel.busy ? "Working..." : "Save Trimmed PNG"
                    enabled: trimModel.can_save
                    onClicked: trimModel.save_trim()
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    radius: 6
                    color: trimModel.error.length > 0 ? "#332728"
                        : trimModel.saved_path.length > 0 ? "#27332c" : "#292f33"
                    border.color: trimModel.error.length > 0 ? "#56383b"
                        : trimModel.saved_path.length > 0 ? "#3b5847" : "#3a444a"

                    Text {
                        anchors.fill: parent
                        anchors.margins: 6
                        text: trimModel.error.length > 0 ? "TRIM ERROR"
                            : trimModel.saved_path.length > 0 ? "SAVED"
                            : trimModel.busy ? "PROCESSING" : trimModel.can_save ? "READY TO SAVE" : "NO IMAGE"
                        color: trimModel.error.length > 0 ? "#dba5a5"
                            : trimModel.saved_path.length > 0 ? "#b2d0b9" : "#b0bbc0"
                        font.bold: true
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: trimModel.error.length > 0 || trimModel.saved_path.length > 0
                    text: trimModel.error.length > 0 ? trimModel.error : trimModel.status
                    color: trimModel.error.length > 0 ? "#dda3a3" : workspace.textMuted
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        // Original-versus-trimmed card preview
        Rectangle {
            Layout.fillWidth: true
            Layout.minimumWidth: 270
            Layout.fillHeight: true
            radius: 10
            color: "#1b1e22"
            border.color: workspace.borderColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "Card Preview"
                        color: workspace.textPrimary
                        font.pixelSize: 20
                        font.bold: true
                    }

                    // Same compact folder action used in Studio.
                    // Trim saves its PNG beside the input image, so that is
                    // the folder to open once a source card has been loaded.
                    Button {
                        id: openTrimFolderButton
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        implicitWidth: 32
                        implicitHeight: 32
                        hoverEnabled: true

                        HoverHandler {
                            enabled: openTrimFolderButton.enabled
                            cursorShape: Qt.PointingHandCursor
                        }

                        ToolTip.visible: hovered
                        ToolTip.delay: 550
                        ToolTip.text: trimModel.source_folder_url.length > 0
                            ? "Open card folder" : "Open output folder"
                        Accessible.name: "Open card folder"

                        onClicked: Qt.openUrlExternally(
                            trimModel.source_folder_url.length > 0
                                ? trimModel.source_folder_url
                                : filePathModel.out_directory
                        )

                        background: Rectangle {
                            radius: 6
                            color: openTrimFolderButton.down ? "#343d42"
                                : openTrimFolderButton.hovered ? "#30383d" : "#252b2f"
                            border.width: 1
                            border.color: openTrimFolderButton.activeFocus
                                ? "#49bb80" : "#42494f"
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

                    TrimButton {
                        text: "Original"
                        implicitHeight: 32
                        enabled: trimModel.preview_url.length > 0 && !trimModel.busy
                        primary: workspace.showOriginal
                        onClicked: workspace.showOriginal = true
                    }

                    TrimButton {
                        text: "Trimmed"
                        implicitHeight: 32
                        enabled: trimModel.preview_url.length > 0 && !trimModel.busy
                        primary: !workspace.showOriginal
                        onClicked: workspace.showOriginal = false
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 8
                    color: "#242a2f"
                    border.color: workspace.borderColor
                    clip: true

                    // Checkerboard makes the new transparent corners visible.
                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            const ctx = getContext("2d");
                            const tile = 18;
                            ctx.fillStyle = "#30353a";
                            ctx.fillRect(0, 0, width, height);
                            ctx.fillStyle = "#282d32";
                            for (let y = 0; y < height; y += tile) {
                                for (let x = 0; x < width; x += tile) {
                                    if (((x / tile) + (y / tile)) % 2 === 0)
                                        ctx.fillRect(x, y, tile, tile);
                                }
                            }
                        }
                    }

                    Image {
                        id: cardImage
                        anchors.fill: parent
                        anchors.margins: 22
                        source: workspace.showOriginal ? trimModel.source_url : trimModel.preview_url
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                        visible: trimModel.preview_url.length > 0
                    }

                    Column {
                        anchors.centerIn: parent
                        width: Math.max(120, parent.width - 55)
                        spacing: 10
                        visible: trimModel.preview_url.length === 0

                        Text {
                            width: parent.width
                            text: trimModel.busy ? "Preparing card preview..." : "No image selected"
                            color: "#c3cbcd"
                            font.pixelSize: 17
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            width: parent.width
                            text: "Open a finished Proxyshop render to preview the trimmed version."
                            color: workspace.textMuted
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: workspace.showOriginal
                        ? "Original export, including print bleed"
                        : "Trimmed card • Transparent rounded corners • 2.5\" × 3.5\""
                    color: workspace.textMuted
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
