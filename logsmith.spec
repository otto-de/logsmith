# -*- mode: python ; coding: utf-8 -*-
import sys

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE

block_cipher = None

assets = [
    ('./app/assets/app_icon.icns', './assets'),
    ('./app/assets/app_icon.png', './assets'),
    ('./app/assets/full.svg', './assets'),
    ('./app/assets/outline.svg', './assets'),
    ('./app/assets/busy.svg', './assets'),
    ('./app/assets/bug.svg', './assets'),
    ('./app/assets/error.svg', './assets'),
    ('./app/assets/valid.svg', './assets'),
    ('./app/assets/invalid.svg', './assets'),
    ('./app/assets/issues.svg', './assets'),
]

app_name = 'logsmith'

a = Analysis(['app/run.py'],
             pathex=['./app'],
             binaries=[],
             datas=assets,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name=app_name,
              debug=False,
              strip=False,
              upx=True,
              runtime_tmpdir=None,
              console=True,
              icon='assets/app_icon.png')
    app = BUNDLE(exe,
                 name=app_name + '.app',
                 info_plist={
                     'NSHighResolutionCapable': 'True',
                     'LSUIElement': True,
                 },
                 icon='./app/assets/app_icon.icns')

if sys.platform == 'linux':
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name=app_name,
              debug=False,
              strip=False,
              upx=True,
              runtime_tmpdir=None,
              console=False,
              icon='./app/assets/app_icon.png')

if sys.platform == 'win32' or sys.platform == 'win64':
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name=app_name,
              debug=False,
              strip=False,
              upx=True,
              runtime_tmpdir=None,
              console=False,
              icon='./app/assets/app_icon.ico')
