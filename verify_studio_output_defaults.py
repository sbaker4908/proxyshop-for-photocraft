"""Optional diagnostic: run with uv run python verify_studio_output_defaults.py."""
from PySide6.QtCore import QSettings

settings = QSettings('ProxyStudio', 'ProxyStudio')
settings.beginGroup('StudioOutputDefaults')
print('Qt settings status:', settings.status())
print('Qt settings location:', settings.fileName())
keys = ['showSetSymbol', 'artistOnlyCredit', 'showWatermark', 'includeFlavorText', 'saveEditablePsd']
for key in keys:
    print(f'  {key}: {settings.value(key, "(not saved)")}')
settings.endGroup()
