# Kclone

Kclone is a self-hosted GitHub-style project manager and build/AI workspace.

## Current milestone

This first release is a Windows desktop foundation. It provides a local project workspace and a place to grow the repository/AI/action/build system.

The project is intentionally self-hosted: your repositories, builds, artifacts, and AI provider configuration can live on your machine.

## Build

On Windows with Python 3.11+:

```powershell
python -m pip install -r requirements.txt
python build.py
```

The executable is written to `dist/Kclone.exe`.

## Roadmap

- Git repository/project manager
- GitHub-style file browser
- AI provider + MCP configuration
- Actions/job runner
- Asset pipeline for PNG and other resources
- ISO build pipeline
- VM testing
- APK/EXE/ISO artifacts
- Phone-accessible web UI
