# -*- mode: python ; coding: utf-8 -*-
import sys
import os

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
    hiddenimports=[],
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
    console=False,
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

if sys.platform == 'darwin':
    icon_path = 'Hackthon/icon.icns'
    if not os.path.exists(icon_path):
        icon_path = None
        
    app = BUNDLE(
        coll,
        name='DesktopPet.app',
        icon=icon_path,
        bundle_identifier='com.desktoppet.app',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'LSUIElement': 'False',
        },
    ) 