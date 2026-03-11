# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['typstwriter/typstwriter.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('typstwriter/icons', 'typstwriter/icons'),
    ],
    hiddenimports=[
        'qtpy',
        'qtpy.QtCore',
        'qtpy.QtWidgets',
        'qtpy.QtGui',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'typstwriter.logging',
        'typstwriter.arguments',
        'typstwriter.configuration',
        'typstwriter.globalstate',
        'typstwriter.mainwindow',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='typstwriter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='typstwriter',
)

app = BUNDLE(
    coll,
    name='typstwriter.app',
    icon=None,
    bundle_identifier='net.posteo.b0.typstwriter',
)