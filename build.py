import PyInstaller.__main__

PyInstaller.__main__.run([
    "kclone.py",
    "--onefile",
    "--windowed",
    "--name=Kclone",
    "--clean",
])
