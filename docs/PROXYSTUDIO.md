# ProxyStudio — Studio and Trim Guide

This guide describes the Studio and Trim additions to the PhotoCraft-based Proxyshop fork. For the original application's installation, configuration, supported templates, attribution, and licenses, see the repository [README](../README.md). The original toolbar **Render** action, Templates tab, and Batch mode are still available.

## Start

Run the app from the project directory on Windows:

```powershell
uv run main.py
```

PhotoCraft, the card templates, and required fonts must be installed as described in the main README. The Studio and Trim tabs are part of the application's Qt/QML interface; they do not require the old one-time ZIP patch installers once the code is checked out from Git.

## Studio — edit and render a card

1. Open **Studio** and search for a card using the Scryfall lookup.
2. Review the populated card details and artwork. You can edit names, mana costs, type lines, rules text, flavor text, power/toughness, artist, and printing details. You can also substitute your own artwork.
3. Select an **installed, compatible template** in the right panel. The **Borderless** template exposes additional options: textbox size, textless mode, and text drop shadow.
4. In **Output**, choose whether to **Include flavor text**. Turning this off excludes flavor text from the finished card but leaves it visible and editable in the form.
5. Choose ordinary image output or **Manual edit in PhotoCraft**, then render using Studio's action button. Successful image renders appear in Card Preview; PSD exports remain in the output folder and open in PhotoCraft for manual editing.

**Manual edit:** the toggle saves a *layered PSD* and launches that saved file in PhotoCraft. It does not automatically create a `.pcraft` file. To use PhotoCraft's native format, choose Save As in PhotoCraft. The PSD remains in the output folder. This Studio operation does not replace the application's original manual-edit pause mechanism.

**Preview badges:** **CURRENT PREVIEW** means the displayed image matches the corresponding Studio editor state at the last successful render; **NEEDS RENDER** means something relevant has changed; **PSD EXPORTED** indicates a current editable PSD rather than a bitmap preview. Changing template settings invalidates the relevant previous preview.

## Front and back faces

For supported Scryfall **Transform** and **modal double-faced (MDFC)** cards, Studio provides **Front** and **Back** tabs. Each side has its own editable text, artwork, and Include flavor text choice. The Render Both Faces action submits separate render jobs through Proxyshop's normal queue; the preview tabs let you inspect both outputs. Edits to one face invalidate *only that face's* image preview. Shared template and Borderless settings apply to both faces, so changing them makes both previews stale.

The initial two-sided Studio implementation is for standard Transform and MDFC layouts. Specialized transforming planeswalkers, Battles, Sagas, Meld, and other unusual layouts are not covered by that implementation.

**Tip:** both sides require compatible, locally installed template files. In particular, the Normal template uses `tf-front.psd` and `tf-back.psd` for ordinary Transform cards, and `mdfc-front.psd` and `mdfc-back.psd` for MDFCs. The Borderless template uses `borderless-vector.psd` for both supported faces. A missing PSD means rendering cannot be prepared even when the template appears in the picker.

## Borderless and MDFC text fitting

The Borderless template supports automatic sizing and Short, Medium, Normal, and Tall textbox choices, as well as textless mode and text drop shadow. The MDFC text-fitting adjustment prevents the rules/flavor text from extending into the bottom strip showing the other face's type or ability. If changing a textbox option produces an unexpected result, try **Automatic** and render again.

The template binary files are downloaded separately and may contain PhotoCraft-specific adjustments. Consult [Template patches](template-patches.md) before replacing them with versions from another Proxyshop fork.

## Trim — print-sized image output

The **Trim** tab accepts an untrimmed card image with the expected bleed. It removes approximately 1/8 inch of bleed per side from a 2.75 × 3.75 inch source, produces a 2.5 × 3.5 inch card image with antialiased transparent rounded corners, and saves a separate PNG alongside the original with a `_trim.png` suffix. The source file is not modified. The **Original / Trimmed** preview switch compares the images, and the adjacent folder button opens the source/output location.

The trimmed image has **no print bleed**; retain the untrimmed original for printing processes that require it. The tool rejects inputs that do not match the expected bleed proportions rather than cropping arbitrary pictures.

## Common issues

- **Render fails immediately, or the log says a PSD template is unavailable:** check the Templates tab and Updater for missing front/back PSDs. See the README's template source and download instructions. A Google Drive message about a private file or request quota may reflect a download refusal, not a bug in Studio's front/back data handling.
- **A preview says NEEDS RENDER:** changes to text, art, template choice, or applicable output options require rendering again. Switching face tabs alone should not mark an unchanged face stale.
- **PSD exported but not visible in image preview:** this is expected; PSDs are meant for layered editing in PhotoCraft. Use the folder icon to locate the file.
- **PhotoCraft did not open automatically:** check that the PhotoCraft desktop app is installed and discoverable. The successfully exported PSD should still be in the output folder.
- **Need the old file-based workflow:** use the original top-right Render button or Batch mode; Studio does not replace those features.

## Development notes

Studio is designed to call Proxyshop's established rendering pipeline and template system rather than replace them. The one-time `README*.txt` files generated during incremental ZIP-based development were consolidated into this guide; the actual code and historical commits remain in Git. Do not mistake those historical installation notes for steps required when cloning a current version of the project.

For upstream provenance and licensing, see [README.md](../README.md) and [LICENSE.md](../LICENSE.md).
