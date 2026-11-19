// Main application window: wires QML views to the Python models and handles global shortcuts.

pragma ComponentBehavior: Bound
import QtCore
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import qml.components
import qml.dialogs
import qml.views

ApplicationWindow {
    id: appWindow

    // ProxyStudio navigation: Studio / Trim primary; legacy tools in menu.
    property int currentModeIndex: 2  // Always open Studio first.
    property bool pluginUpdateAvailable: false
    property bool templateUpdateAvailable: false
    property QtObject currentRenderingModel: currentModeIndex === 1 ? batchRenderModel : templateListModel

    title: "MTG Proxy Studio"
    width: 800
    height: 640
    visible: true
    color: appSystemPalette.window

    SystemPalette {
        id: appSystemPalette
    }

    FontLoader {
        id: emojiFontLoader
        source: "file:///C:/Windows/Fonts/seguiemj.ttf"
        //source: "file:///C:/Windows/Fonts/seguisym.ttf"
    }

    FontLoader {
        id: monospaceFontLoader
        source: "file:///C:/Windows/Fonts/CascadiaMono.ttf"
    }

    Settings {
        id: settings

        category: "App"
        location: filePathModel.get_preferences_path("App.ini")

        // UI sizing preferences
        property alias windowWidth: appWindow.width
        property alias windowHeight: appWindow.height
        property alias windowX: appWindow.x
        property alias windowY: appWindow.y
        property var rootSplitState
        property var templateListSplitState

        // Model preferences
        property string selectedTemplateName
        property string batchModeTemplateSelections
    }

    Timer {
        id: photocraftPromptTimer
        interval: 250
        repeat: false
        running: photocraftSetupModel.required
        onTriggered: photocraftFileDialog.open()
    }

    Component.onCompleted: {
        rootSplit.restoreState(settings.rootSplitState);
        templateListSplit.restoreState(settings.templateListSplitState);

        if (settings.selectedTemplateName)
            templateListModel.select_template(settings.selectedTemplateName);
        if (settings.batchModeTemplateSelections)
            batchRenderModel.restore_template_selections(settings.batchModeTemplateSelections);
    }
    Component.onDestruction: {
        settings.rootSplitState = rootSplit.saveState();
        settings.templateListSplitState = templateListSplit.saveState();

        settings.selectedTemplateName = templateListModel.selected_template_name();
        settings.batchModeTemplateSelections = batchRenderModel.get_template_selections_json();

        settingsTreeModel.save_configs();
        templateUpdaterModel.save_versions();
    }

    function updateRenderQueueSize() {
        const rCount = renderOperationsModel.rowCount();
        if (rCount != renderOperationsConnections.renderQueueSize)
            renderOperationsConnections.renderQueueSize = rCount;
    }

    Connections {
        id: renderOperationsConnections

        property int renderQueueSize: 0

        target: renderOperationsModel

        function onRowsInserted() {
            appWindow.updateRenderQueueSize();
        }
        function onRowsRemoved() {
            appWindow.updateRenderQueueSize();
        }
    }

    DropArea {
        anchors.fill: parent
        onDropped: drop => {
            if (drop.hasUrls)
                appWindow.currentRenderingModel.render_targets(drop.urls);
        }
    }

    menuBar: MenuBar {
        id: menuBar
        // ProxyStudio navigation: left-aligned Studio and Trim.
        // Reserve space for both mode buttons and the separator; menu items
        // then begin with File, Tools, Help. The usual menu order is unchanged.
        leftPadding: 190

        background.implicitHeight: 0
        background.implicitWidth: 0

        delegate: MenuBarItem {
            id: menuBarItem

            leftPadding: 8
            rightPadding: 8
            topPadding: 7
            bottomPadding: 7
            background: Rectangle {
                color: menuBarItem.down || menuBarItem.highlighted ? appSystemPalette.text : "transparent"
                opacity: menuBarItem.down ? 0.1 : 0.05
            }
        }

        CustomMenu {
            systemPalette: appSystemPalette
            title: "File"

            Action {
                text: "Render..."
                onTriggered: appWindow.currentRenderingModel.render_selections()
            }
            MenuSeparator {}
            Action {
                text: "Open app directory"
                onTriggered: Qt.openUrlExternally(filePathModel.app_root)
            }
            Action {
                text: "Open output directory"
                onTriggered: Qt.openUrlExternally(filePathModel.out_directory)
            }
            Action {
                text: "Open templates directory"
                onTriggered: Qt.openUrlExternally(filePathModel.templates_directory)
            }
            Action {
                text: "Open plugins directory"
                onTriggered: Qt.openUrlExternally(filePathModel.plugins_directory)
            }
        }
        CustomMenu {
            systemPalette: appSystemPalette
            title: appWindow.pluginUpdateAvailable || appWindow.templateUpdateAvailable ? "Tools •" : "Tools"

            // Primary workflows live in the app bar; advanced workflows live here.
            Action {
                text: "Templates (legacy)"
                onTriggered: appWindow.currentModeIndex = 0
            }
            Action {
                text: "Batch mode (legacy)"
                onTriggered: appWindow.currentModeIndex = 1
            }
            MenuSeparator {}
            Action {
                text: appWindow.pluginUpdateAvailable ? "Plugins  •  Update available" : "Plugins..."
                onTriggered: {
                    appWindow.pluginUpdateAvailable = false;
                    if (pluginUpdaterLoader.active)
                        pluginUpdaterLoader.item?.show();
                    else
                        pluginUpdaterLoader.active = true;
                }
            }
            Action {
                text: appWindow.templateUpdateAvailable ? "Template updater  •  Update available" : "Template updater..."
                onTriggered: {
                    appWindow.templateUpdateAvailable = false;
                    appWindow.currentModeIndex = 4;
                }
            }
            MenuSeparator {}

            Action {
                text: "Transform images"
                onTriggered: {
                    if (imageTransformLoader.active) {
                        imageTransformLoader.item?.show();
                    } else {
                        imageTransformLoader.active = true;
                    }
                }
            }
            Action {
                text: "Preview system palette"
                onTriggered: {
                    if (systemPaletteViewerLoader.active) {
                        systemPaletteViewerLoader.item?.show();
                    } else {
                        systemPaletteViewerLoader.active = true;
                    }
                }
            }
            Action {
                text: "Preview fonts"
                onTriggered: {
                    if (fontViewerLoader.active) {
                        fontViewerLoader.item?.show();
                    } else {
                        fontViewerLoader.active = true;
                    }
                }
            }
            MenuSeparator {}
            CustomMenu {
                systemPalette: appSystemPalette
                title: "Tests"
                implicitWidth: 270

                Action {
                    text: "Test all"
                    onTriggered: testRendersModel.test_all("", false)
                }
                Action {
                    text: "Quick test all"
                    onTriggered: testRendersModel.test_all("", true)
                }

                CustomMenu {
                    id: testAllLayoutsSubMenu

                    systemPalette: appSystemPalette
                    title: "Test all with layout"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenuItem {
                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            text: modelData
                            onTriggered: testRendersModel.test_all(modelData, false)
                        }

                        onObjectAdded: (index, object) => testAllLayoutsSubMenu.insertItem(index, object)
                        onObjectRemoved: (index, object) => testAllLayoutsSubMenu.removeItem(object)
                    }
                }
                CustomMenu {
                    id: quickTestAllLayoutsSubMenu

                    systemPalette: appSystemPalette
                    title: "Quick test all with layout"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenuItem {
                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            text: modelData
                            onTriggered: testRendersModel.test_all(modelData, true)
                        }

                        onObjectAdded: (index, object) => quickTestAllLayoutsSubMenu.insertItem(index, object)
                        onObjectRemoved: (index, object) => quickTestAllLayoutsSubMenu.removeItem(object)
                    }
                }
                CustomMenu {
                    id: testAllWithSpecificTestCaseSubMenu

                    systemPalette: appSystemPalette
                    title: "Test all with test case"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenu {
                            id: testAllWithSpecificLayoutTestCaseSubMenu

                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            title: modelData

                            Instantiator {
                                model: testRendersModel.get_test_cases_for_layout(testAllWithSpecificLayoutTestCaseSubMenu.modelData)

                                delegate: CustomMenuItem {
                                    required property int index
                                    required property string modelData

                                    systemPalette: appSystemPalette
                                    text: modelData
                                    onTriggered: testRendersModel.test_all(testAllWithSpecificLayoutTestCaseSubMenu.modelData, false, modelData)
                                }

                                onObjectAdded: (index, object) => testAllWithSpecificLayoutTestCaseSubMenu.insertItem(index, object)
                                onObjectRemoved: (index, object) => testAllWithSpecificLayoutTestCaseSubMenu.removeItem(object)
                            }
                        }

                        onObjectAdded: (index, object) => testAllWithSpecificTestCaseSubMenu.insertMenu(index, object)
                        onObjectRemoved: (index, object) => testAllWithSpecificTestCaseSubMenu.removeMenu(object)
                    }
                }

                MenuSeparator {}

                Action {
                    text: "Test selected template(s)"
                    onTriggered: appWindow.currentRenderingModel.test_render("", false)
                }
                Action {
                    text: "Quick test selected template(s)"
                    onTriggered: appWindow.currentRenderingModel.test_render("", true)
                }

                CustomMenu {
                    id: selectedTemplateLayoutsSubMenu

                    systemPalette: appSystemPalette
                    title: "Test selected template(s) with layout"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenuItem {
                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            text: modelData
                            onTriggered: appWindow.currentRenderingModel.test_render(modelData, false)
                        }

                        onObjectAdded: (index, object) => selectedTemplateLayoutsSubMenu.insertItem(index, object)
                        onObjectRemoved: (index, object) => selectedTemplateLayoutsSubMenu.removeItem(object)
                    }
                }
                CustomMenu {
                    id: selectedTemplateQuickLayoutsSubMenu

                    systemPalette: appSystemPalette
                    title: "Quick test selected template(s) with layout"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenuItem {
                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            text: modelData
                            onTriggered: appWindow.currentRenderingModel.test_render(modelData, true)
                        }

                        onObjectAdded: (index, object) => selectedTemplateQuickLayoutsSubMenu.insertItem(index, object)
                        onObjectRemoved: (index, object) => selectedTemplateQuickLayoutsSubMenu.removeItem(object)
                    }
                }
                CustomMenu {
                    id: selectedTemplateSpecificTestCaseSubMenu

                    systemPalette: appSystemPalette
                    title: "Test selected template(s) with test case"

                    Instantiator {
                        model: testRendersModel.layout_categories

                        delegate: CustomMenu {
                            id: selectedTemplateSpecificLayoutTestCaseSubMenu

                            required property int index
                            required property string modelData

                            systemPalette: appSystemPalette
                            title: modelData

                            Instantiator {
                                model: testRendersModel.get_test_cases_for_layout(selectedTemplateSpecificLayoutTestCaseSubMenu.modelData)

                                delegate: CustomMenuItem {
                                    required property int index
                                    required property string modelData

                                    systemPalette: appSystemPalette
                                    text: modelData
                                    onTriggered: appWindow.currentRenderingModel.test_render(selectedTemplateSpecificLayoutTestCaseSubMenu.modelData, false, modelData)
                                }

                                onObjectAdded: (index, object) => selectedTemplateSpecificLayoutTestCaseSubMenu.insertItem(index, object)
                                onObjectRemoved: (index, object) => selectedTemplateSpecificLayoutTestCaseSubMenu.removeItem(object)
                            }
                        }

                        onObjectAdded: (index, object) => selectedTemplateSpecificTestCaseSubMenu.insertMenu(index, object)
                        onObjectRemoved: (index, object) => selectedTemplateSpecificTestCaseSubMenu.removeMenu(object)
                    }
                }
            }
        }
        CustomMenu {
            systemPalette: appSystemPalette
            title: "Help"

            Action {
                text: `<font face="${emojiFontLoader.name}">🌐</font> Project GitHub`
                onTriggered: Qt.openUrlExternally(github_url)
            }
            Action {
                text: `<font face="${emojiFontLoader.name}">❔</font>  Frequently asked questions`
                onTriggered: Qt.openUrlExternally(`${github_url}#-faq`)
            }
            Action {
                text: `<font face="${emojiFontLoader.name}">🪲</font>  Report an issue`
                onTriggered: Qt.openUrlExternally(`${github_url}/issues`)
            }
        }

        // Primary modes at the left, before the File / Tools / Help menus.
        RowLayout {
            parent: menuBar
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            spacing: 4

            // Studio and Trim are the two visible, first-class workflows.
            Button {
                id: studioNavigationButton
                text: "Studio"
                implicitWidth: 86
                implicitHeight: 30
                hoverEnabled: enabled
                onClicked: appWindow.currentModeIndex = 2
                HoverHandler {
                    enabled: studioNavigationButton.enabled
                    cursorShape: Qt.PointingHandCursor
                }
                contentItem: Text {
                    text: studioNavigationButton.text
                    color: appWindow.currentModeIndex === 2 ? "#dcf8e8" : "#c7d0d5"
                    font.pixelSize: 13
                    font.bold: appWindow.currentModeIndex === 2
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: appWindow.currentModeIndex === 2 ? "#23583f"
                        : studioNavigationButton.hovered ? "#323a40" : "transparent"
                    border.width: 1
                    border.color: appWindow.currentModeIndex === 2 ? "#4aa876" : "transparent"
                }
            }
            Button {
                id: trimNavigationButton
                text: "Trim"
                implicitWidth: 76
                implicitHeight: 30
                hoverEnabled: enabled
                onClicked: appWindow.currentModeIndex = 3
                HoverHandler {
                    enabled: trimNavigationButton.enabled
                    cursorShape: Qt.PointingHandCursor
                }
                contentItem: Text {
                    text: trimNavigationButton.text
                    color: appWindow.currentModeIndex === 3 ? "#dcf8e8" : "#c7d0d5"
                    font.pixelSize: 13
                    font.bold: appWindow.currentModeIndex === 3
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: appWindow.currentModeIndex === 3 ? "#23583f"
                        : trimNavigationButton.hovered ? "#323a40" : "transparent"
                    border.width: 1
                    border.color: appWindow.currentModeIndex === 3 ? "#4aa876" : "transparent"
                }
            }
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 21
                Layout.leftMargin: 5
                Layout.rightMargin: 5
                color: "#485157"
            }
        }

        // The existing queue / render / settings actions stay on the right.
        RowLayout {
            parent: menuBar
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 7
            spacing: 4

            CustomButton {
                systemPalette: appSystemPalette
                implicitHeight: 30
                text: `<font face="${emojiFontLoader.name}">⏩</font> Queue (${renderOperationsConnections.renderQueueSize})`
                onClicked: {
                    if (renderQueueLoader.active)
                        renderQueueLoader.item?.show();
                    else
                        renderQueueLoader.active = true;
                }
            }
            CustomButton {
                systemPalette: appSystemPalette
                implicitHeight: 30
                text: renderOperationsModel.is_rendering
                    ? `<font face="${emojiFontLoader.name}">🚫</font> Cancel`
                    : `<font face="${emojiFontLoader.name}">⏯️</font> Resume`
                enabled: renderOperationsConnections.renderQueueSize || renderOperationsModel.is_rendering
                onClicked: renderOperationsModel.is_rendering
                    ? renderOperationsModel.cancel() : renderOperationsModel.resume()
            }
            CustomButton {
                id: renderButton
                systemPalette: appSystemPalette
                implicitHeight: 30
                text: `<font face="${emojiFontLoader.name}">▶️</font> Render`
                onClicked: appWindow.currentRenderingModel.render_selections()
            }
            CustomButton {
                id: settingsButton
                systemPalette: appSystemPalette
                implicitHeight: 30
                text: `<font face="${emojiFontLoader.name}">⚙️</font> Settings`
                onClicked: openSettings()

                // TemplateList still uses this function via openSettings.
                function openSettings(templateName = "", className = "", pluginName = ""): void {
                    settingsTreeModel.select_settings_section(templateName, className, pluginName);
                    if (settingsWindowLoader.active)
                        settingsWindowLoader.item?.show();
                    else
                        settingsWindowLoader.active = true;
                }
            }
        }

    }

    Connections {
        target: pluginUpdaterModel
        function onUpdateAvailable() {
            appWindow.pluginUpdateAvailable = true;
        }
    }
    Connections {
        target: templateUpdaterModel
        function onUpdateAvailable() {
            appWindow.templateUpdateAvailable = true;
        }
    }

    CustomMessageDialog {
        id: renderMessageDialog

        dialogContentModel: renderMessageDialogContentModel
    }

    Window {
        id: manualEditOverlay

        visible: renderMessageDialogContentModel.manual_edit_overlay_visible
        x: renderMessageDialogContentModel.manual_edit_overlay_x
        y: renderMessageDialogContentModel.manual_edit_overlay_y
        width: renderMessageDialogContentModel.manual_edit_overlay_width
        height: renderMessageDialogContentModel.manual_edit_overlay_height
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
        color: "transparent"
        title: "Proxyshop manual editing"

        Rectangle {
            anchors.fill: parent
            radius: 10
            color: "#ED141414"
            border.color: "#80FFFFFF"
            border.width: 1

            Column {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 6

                Text {
                    text: renderMessageDialogContentModel.manual_edit_overlay_title
                    color: "white"
                    font.pixelSize: 17
                    font.bold: true
                }

                Text {
                    width: parent.width
                    text: renderMessageDialogContentModel.manual_edit_overlay_text
                    color: "#E8E8E8"
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                }

                Text {
                    width: parent.width
                    text: "Double-click to hide"
                    color: "#B0B0B0"
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignRight
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onDoubleClicked: renderMessageDialogContentModel.hide_manual_edit_overlay()
        }

        Timer {
            interval: 500
            repeat: true
            running: manualEditOverlay.visible
            onTriggered: renderMessageDialogContentModel.refresh_manual_edit_overlay()
        }
    }

    Connections {
        id: renderMessageDialogConnections

        target: renderMessageDialogContentModel
        function onDialogRequested(): void {
            if (renderMessageDialog.visible) {
                renderMessageDialog.accept();
            }
            renderMessageDialog.open();
        }
    }

    FileDialog {
        id: photocraftFileDialog
        title: "Locate PhotoCraft"
        fileMode: FileDialog.OpenFile
        nameFilters: [
            "PhotoCraft CLI (photocraft-cli.exe)",
            "PhotoCraft (photocraft.exe)",
            "Executables (*.exe)",
            "All (*)"
        ]
        onAccepted: photocraftSetupModel.set_path(selectedFile.toString())
        onRejected: photocraftSetupModel.cancel()
    }

    Connections {
        target: photocraftSetupModel

        function onErrorChanged(): void {
            if (photocraftSetupModel.required && photocraftSetupModel.error.length > 0)
                photocraftFileDialog.open();
        }
    }

    CustomFileDialog {
        dialogModel: fileDialogModel
        settings: settings
    }

    Loader {
        id: settingsWindowLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("views/SettingsWindow.qml", {
                systemPalette: appSystemPalette,
                pathModel: filePathModel,
                emojiFontName: emojiFontLoader.name,
                settingsTreeModel: settingsTreeModel,
                settingsModel: settingsModel
            });
        }
    }

    Loader {
        id: pluginUpdaterLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("views/PluginUpdater.qml", {
                systemPalette: appSystemPalette,
                emojiFontName: emojiFontLoader.name,
                updaterModel: pluginUpdaterModel,
                pathModel: filePathModel
            });
        }
    }

    Loader {
        id: renderQueueLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("views/RenderQueue.qml", {
                systemPalette: appSystemPalette,
                emojiFontName: emojiFontLoader.name,
                queueModel: renderOperationsModel,
                pathModel: filePathModel
            });
        }
    }

    Loader {
        id: imageTransformLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("tools/ImageTransformWindow.qml", {
                systemPalette: appSystemPalette,
                transformModel: imageTransformModel
            });
        }
    }

    Loader {
        id: systemPaletteViewerLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("tools/SystemPaletteViewer.qml");
        }
    }

    Loader {
        id: fontViewerLoader

        active: false
        asynchronous: true
        onLoaded: item.show()

        Component.onCompleted: {
            setSource("tools/FontViewer.qml");
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        SplitView {
            id: rootSplit

            Layout.fillHeight: true
            Layout.fillWidth: true

            orientation: Qt.Vertical

            StackLayout {
                SplitView.fillHeight: true
                SplitView.fillWidth: true

                currentIndex: appWindow.currentModeIndex

                Rectangle {
                    color: appSystemPalette.window
                    Layout.fillHeight: true
                    Layout.fillWidth: true

                    SplitView {
                        id: templateListSplit

                        anchors.fill: parent
                        orientation: Qt.Horizontal

                        TemplateList {
                            SplitView.fillWidth: true
                            SplitView.fillHeight: true

                            systemPalette: appSystemPalette
                            templateListMdl: templateListModel
                            openSettings: settingsButton.openSettings
                        }
                        TemplateDetails {
                            SplitView.minimumWidth: 100
                            SplitView.preferredWidth: 200

                            systemPalette: appSystemPalette
                            templateListMdl: templateListModel
                            pathModel: filePathModel
                        }
                    }
                }
                BatchRenderView {
                    Layout.fillHeight: true
                    Layout.fillWidth: true

                    systemPalette: appSystemPalette
                    batchModel: batchRenderModel
                    pathModel: filePathModel
                }
                Loader {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: "views/StudioWorkspace.qml"
                }
                Loader {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: "views/TrimWorkspace.qml"
                }
                // ProxyStudio: Embedded template updater (same window).
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 48
                        color: "#1d2124"
                        border.color: "#363e43"
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 18
                            anchors.rightMargin: 18
                            spacing: 10
                            Text {
                                text: "Template Updater"
                                font.pixelSize: 20
                                font.bold: true
                                color: "#f5f6f7"
                            }
                            Item { Layout.fillWidth: true }
                            CustomButton {
                                systemPalette: appSystemPalette
                                text: "Refresh"
                                implicitHeight: 32
                                enabled: !templateUpdaterModel.fetching_data
                                onClicked: templateUpdaterModel.fetch_data()
                            }
                            CustomButton {
                                systemPalette: appSystemPalette
                                text: "Back to Studio"
                                implicitHeight: 32
                                onClicked: appWindow.currentModeIndex = 2
                            }
                        }
                    }
                    Loader {
                        id: embeddedTemplateUpdaterLoader
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        active: appWindow.currentModeIndex === 4
                        asynchronous: true
                        Component.onCompleted: {
                            setSource("views/TemplateUpdaterEmbedded.qml", {
                                systemPalette: appSystemPalette,
                                updaterModel: templateUpdaterModel,
                                pathModel: filePathModel
                            });
                        }
                    }
                }

            }
            Console {
                visible: appWindow.currentModeIndex < 2
                
                SplitView.preferredHeight: 200
                SplitView.fillWidth: true

                systemPalette: appSystemPalette
                logModel: consoleModel
                pathModel: filePathModel
                emojiFontFamily: emojiFontLoader.name
                monospaceFontFamily: monospaceFontLoader.name
            }
        }
    }
}
