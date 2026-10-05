import PyInstaller.__main__

PyInstaller.__main__.run([
    "kclone.py",
    "--onefile",
    "--windowed",
    "--name=Kclone",
    "--add-data=kclone_mcp_server.py;.",
    "--clean",
])

PyInstaller.__main__.run([
    "kclone_mcp_server.py",
    "--onefile",
    "--console",
    "--name=Kclone-MCP",
    "--clean",
])
