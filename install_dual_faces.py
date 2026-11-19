"""Install the Studio Front/Back bridge without overwriting local main.py changes.

Run once from the ProxyStudio project root:
    uv run python install_dual_faces.py
Safe to rerun; it verifies each insertion and avoids duplication.
"""
from __future__ import annotations

from pathlib import Path


def install() -> None:
    main = Path(__file__).resolve().parent / "main.py"
    if not main.is_file():
        raise FileNotFoundError("Place install_dual_faces.py in the repository root beside main.py")
    source = main.read_text(encoding="utf-8")

    if 'from src.gui.qml.models.studio_dual_render_model import StudioDualRenderModel' not in source:
        anchor = '    from src.gui.qml.models.studio_card_model import StudioCardModel\n'
        if source.count(anchor) != 1:
            raise ValueError("Could not locate StudioCardModel import in main.py; nothing changed")
        source = source.replace(anchor, anchor + '    from src.gui.qml.models.studio_dual_render_model import StudioDualRenderModel\n')

    if '    studio_dual_render_model = StudioDualRenderModel(' not in source:
        anchor = '    root_context = engine.rootContext()\n'
        if source.count(anchor) != 1:
            raise ValueError("Could not find the QML root context; nothing changed")
        block = '''    studio_dual_render_model = StudioDualRenderModel(
        card_model=studio_card_model,
        template_list_model=template_list_model,
        plugin_library=plugin_library,
        render_queue=render_queue,
        file_dialog_model=file_dialog_model,
        message_dialog_model=render_message_dialog_content_model,
    )

'''
        source = source.replace(anchor, block + anchor)

    if 'root_context.setContextProperty("studioDualRenderModel", studio_dual_render_model)' not in source:
        anchor = '    root_context.setContextProperty("studioRenderModel", studio_render_model)\n'
        if source.count(anchor) != 1:
            raise ValueError("Could not find Studio render context property; nothing changed")
        source = source.replace(anchor, anchor + '    root_context.setContextProperty("studioDualRenderModel", studio_dual_render_model)\n')

    compile(source, str(main), "exec")
    if main.read_text(encoding="utf-8") == source:
        print("Already installed: Studio dual-face bridge is present.")
        return
    # Back up under .git so a later `git add .` cannot accidentally commit it.
    backup_folder = main.parent / ".git"
    backup = backup_folder / "proxystudio_main_pre_dual.py" if backup_folder.is_dir() else None
    if backup is not None and not backup.exists():
        backup.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    main.write_text(source, encoding="utf-8")
    print("Studio dual-face bridge added to main.py.")
    if backup is not None:
        print("The original main.py was backed up inside .git.")


if __name__ == "__main__":
    install()
