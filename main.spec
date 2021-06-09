# -*- mode: python ; coding: utf-8 -*-

import os
import json
import shutil



block_cipher = None


a = Analysis(['main.py'],
             pathex=['./'],
             binaries=[],
             datas=[('templates','templates'),('version.json','.')],
             hiddenimports=[],
             hookspath=['./hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=f'ComicTools',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          icon='./icon.ico',
          console=True )

shutil.copyfile('config.json.template', '{0}/config.json'.format(DISTPATH))
shutil.copyfile('comicdb.json', '{0}/comicdb.json'.format(DISTPATH))
shutil.copyfile('comicutil.json', '{0}/comicutil.json'.format(DISTPATH))
