#!/usr/bin/env python3
"""
Claude Code Hook: Pre-Bash Command Validator.

Validates bash commands before execution.
"""

import json
import shutil
import sys


def validate_before_execution(command: str) -> list[str]:
    """Validate bash command before execution."""
    issues = []

    # If uv is not installed, don't block commands that would otherwise require it.
    if shutil.which("uv") is None:
        return issues

    if command.startswith("python"):
        issues.append("Please use `uv run python ...`")

    return issues


def main():
    """Main entry point for the hook."""
    # Read hook input from stdin
    hook_input = json.load(sys.stdin)

    # Extract the command from tool_input
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    # Validate the command
    issues = validate_before_execution(command)

    # Output the decision using hookSpecificOutput format required by PreToolUse
    if issues:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "\n".join(issues),
            }
        }
    else:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }

    print(json.dumps(result))


if __name__ == "__main__":
    main()