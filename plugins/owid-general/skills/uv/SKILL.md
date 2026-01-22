---
description: We always use `uv` for running python scripts (both standalone and complex python projects) and managing python dependencies. Always use this instead of running system `python`, `python3`, `pip` or `pip3`
globs:
  - "*.py"
  - "pyproject.toml"
  - "requirements*.txt"
allowed-tools:
- "Bash(uv add:*)"
- "Bash(uv remove:*)"
- "Bash(uv sync:*)"
- "Bash(uv pip:*)"
- "Bash(uv init:*)"
- "Bash(uv tree:*)"
- "Bash(uv pip:*)"
---

# Using uv for Python

When running Python code or managing Python dependencies, always use `uv` instead of `pip` or `python` directly.

`uv` should be installed - if it is not, ask the user to `brew install uv` or similar depending on their OS. Offer to do it on their behalf.

If you are running in sandbox mode, tell the user that you want to add the uv cache directory to the list of allowed paths, by adding the snippet below to the PROJECTDIR/.claude/settings.local.json file. Once this is done, uv will be able to read and write its cache even in sandbox mode.

```json
{
  "permissions": {
    "allow": [
        "Read(~/.cache/uv)",
        "Edit(~/.cache/uv)",
        // other allowed paths...
    ],
  }
}
```

## Preferred python version

The preferred default python version to use and set up for projects is 3.12.

Write code using type hints.

For projects or very complex standalone scripts, set up ruff (linter/formatter) and ty (type checker) as dev dependencies and run both when you make changes to python source code.

## Python projects vs standalone scripts

For python projects with dependencies, always use `uv` to manage dependencies (`uv init`, `uv add`, `uv sync`, etc) and run scripts (`uv run`).

For standalone scripts, use comment headers to specify dependencies like so:
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
# rest of your python script comes below
```

## Running Python standalone scripts

Instead of:
```bash
python script.py
```

Use:
```bash
uv run --script script.py
```

## Running third party tools/scripts

For one-off tool execution:
```bash
uv tool run <tool-name>
# or shorthand
uvx <tool-name>
```

## Extended documentation

For complex interactions with uv or to debug uv issues, refer to the online documentation at https://docs.astral.sh/uv/llms.txt and the pages linked from there. This is not necessary to just run scripts, add dependencies etc.