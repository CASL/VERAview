# -*- mode: python -*-
a = Analysis(['veraview.py', 'veraview.spec'],
             pathex=['/Users/re7x/src/casl-dev/veraview'],
             hiddenimports=[ '_proxy', 'utils', 'defs', 'h5ac' ],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='veraview',
          debug=True,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='veraview')

app = BUNDLE( exe, appname = 'VeraView', version = '0.5.0' )
