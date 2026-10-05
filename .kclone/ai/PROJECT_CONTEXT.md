# Kclone AI Project Context

Kclone is designed to create and develop operating systems.

The AI should treat the opened project as a complete workspace: source tree, local tree, assets, build configuration, tests, and generated artifacts are all related.

## OS build goal

The normal target is a bootable ISO. The agent should inspect the current project before changing it, validate assets and build inputs, build the ISO, test it in a VM when available, inspect failures, repair the project, and rebuild.

## Assets

Local PNGs and other supported image assets are first-class inputs. They may be added to assets/icons, assets/wallpapers, assets/boot, or assets/ui. The build pipeline should use their actual paths instead of requiring manual copying into generated build directories.

## Project lifecycle

The agent may create new files/directories, inspect existing projects, modify old projects, and evolve the OS tree over time. Git branches and commits should be used to preserve changes.

## MCP

MCP configuration belongs in .kclone/mcp. Connected MCP tools are project context, not an unrelated chat feature.
