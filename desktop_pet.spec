# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Hackthon/desktop_pet.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Hackthon/idle.gif', 'Hackthon'),
        ('Hackthon/happy.gif', 'Hackthon'),
        ('Hackthon/moving.gif', 'Hackthon'),
        ('Hackthon/ui_style.py', 'Hackthon'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Changed to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DesktopPet',
)

app = BUNDLE(
    coll,
    name='DesktopPet.app',
    icon='icon.icns',
    bundle_identifier='com.desktoppet.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',  # Changed to False to ensure window appears
        'LSUIElement': 'False',  # Changed to False to ensure window appears
    },
) 