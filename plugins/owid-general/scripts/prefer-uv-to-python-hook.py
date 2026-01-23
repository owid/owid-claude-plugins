#!/usr/bin/env -S uv run --script
"""
Claude Code Hook: Pre-Bash Command Validator.

Validates bash commands before execution.
"""

import json
import sys


def validate_before_execution(command: str) -> list[str]:
    """Validate bash command before execution."""
    issues = []

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

    # Output the decision
    if issues:
        result = {"decision": "block", "reason": "\n".join(issues)}
    else:
        result = {"decision": "allow"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()