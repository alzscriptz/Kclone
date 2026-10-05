# Kclone OS Workspace Contract

Kclone OS projects are first-class operating-system workspaces.

## Trees

- Root tree: the versioned project source tree.
- Local tree: the complete local workspace visible to the desktop agent.
- Asset tree: assets/icons, assets/wallpapers, assets/boot, and assets/ui.
- Build tree: build configuration and scripts.
- Artifact tree: generated ISO and other build outputs.

## AI project awareness

An OS project carries a project context file under .kclone/ai/PROJECT_CONTEXT.md and MCP configuration under .kclone/mcp/.

The connected AI is expected to understand the project as a complete system rather than treating individual files independently. It can inspect the tree, create files and directories, modify existing source, update build configuration, add local assets, run validation/build/test workflows, inspect failures, and iterate.

## ISO workflow

The intended workflow is:

1. Inspect the project tree and current build configuration.
2. Inspect and validate required source, boot files, manifests and assets.
3. Accept local PNG and other assets as first-class build inputs.
4. Build the ISO using the project's configured build pipeline.
5. Boot/test the image in a VM when the required VM/build tools exist.
6. Read build/test output.
7. Repair the project and rebuild.
8. Keep the resulting ISO in artifacts/.

## Asset workflow

PNG files can be added from the local computer without manually editing obscure build paths. Kclone should place them into the asset tree and expose their paths and roles to the AI/build pipeline.

## Project lifecycle

The AI can work on existing projects, create new projects, and create additional files/directories in real time. Projects can remain private and can be synchronized with a private GitHub repository.
