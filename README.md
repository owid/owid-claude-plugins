This repository contains tools to help with using Our World In Data data and tooling when using Claude Code. For ease of versioning and use across the team, these are structured as plugins containing mail different skills. The skills themselves might very well be useful for other coding agents as well like OpenAI Codex CLI, but the delivery format is structured around a Claude Code plugin marketplace with multiple plugins.

This project is in an early, experimental stage. Use at your own risk.

## Available plugins

### owid-general

General purpose instructions that we find useful at Our World In Data across projects, regardless of programming language. For example there is a skill that tells agents to use `uv` instead of system `python` for running python code and managing .

## Installing plugins

- In Claude Code, use `/plugin marketplace add owid/owid-claude-plugins`.
- Run `/plugin` and tab to marketplaces, then select `owid-claude-plugins`.
- Browse the available plugins

Some skills or commands may need certain prerequisites installed (e.g. `uv` to run python scripts and manage dependencies). You can either install these manually when a skills fails because of a missing tool (e.g. with `brew install uv`); or you can use this command in your terminal to install all common tools required by skills in this repo:

```bash
curl -sSL https://raw.githubusercontent.com/owid/owid-skills/main/install-prerequisites-macos.sh | bash
```

## Development

When adding new skills or plugins, consider the following:
- Split plugins by use-case. `owid-general` should only contain skills etc that are useful for a wide range of team members or other users. Consider adding new plugins when the consumers of this plugin likely have specific needs (e.g. frontend engineers working on the OWID website; or data scientists working on updating data in our ETL)
- Test your skills/commands/subagents before adding them here.
- Bump plugin versions when you make changes so the update mechanism of Claude Code plugins work properly.
- When you add scripts, try to keep prerequisites small and use what is already available. If it makes sense to require a specific tool to be installed, add installation of it to ./install-prerequisites-macos.sh
