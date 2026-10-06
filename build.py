import os, sys
import PyInstaller.__main__

sep = ";" if os.name == "nt" else ":"
root = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    "kclone.py",
    "--onefile",
    "--windowed",
    "--name=Kclone",
    "--clean",
    "--add-data", f"{os.path.join(root,'kclone_mcp_server.py')}{sep}.",
    "--add-data", f"{os.path.join(root,'templates','os')}{sep}templates/os",
])
