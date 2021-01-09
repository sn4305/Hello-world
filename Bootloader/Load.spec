# -*- mode: python -*-

block_cipher = None


a = Analysis(['Load.py'],
             pathex=['C:\\Users\\e9981231\\Documents\\02 FW\\Python\\CAN\\ZLGCAN\\Bootloader'],
             binaries=[('C:\\Users\\e9981231\\Documents\\02 FW\\Python\\CAN\\ZLGCAN\\Bootloader\\zlgcan.dll','.')],
             datas=[('C:\\Users\\e9981231\\Documents\\02 FW\\Python\\CAN\\ZLGCAN\\Bootloader\\Load.ui','.'),('C:\\Users\\e9981231\\Documents\\02 FW\\Python\\CAN\\ZLGCAN\\Bootloader\\logging.conf','.')],
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
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Load',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Load')
