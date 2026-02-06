#!/bin/bash
# This script installs prerequisite tools for skills in this repository.
# Run it from a terminal like this:
#   curl -sSL https://raw.githubusercontent.com/owid/owid-skills/main/install-prerequisites-macos.sh | bash
set -e

echo "=== OWID macOS Development Tools Installer ==="
echo

# Install Homebrew if not installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add brew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "Homebrew is already installed"
fi

# Define packages: "package_name:command_name" (command defaults to package name)
packages=(
    "uv"
    # "ripgrep-all:rga"
    "ripgrep:rg"
    # "pandoc"
    "jq"
    "gh"
    "duckdb"
    "claude-code:claude"
)

# Build list of missing packages
missing=()
for entry in "${packages[@]}"; do
    package="${entry%%:*}"
    command="${entry#*:}"
    [[ "$command" == "$entry" ]] && command="$package"

    if command -v "$command" &> /dev/null; then
        echo "$package is already installed"
    else
        echo "$package needs to be installed"
        missing+=("$package")
    fi
done

# Install all missing packages in one call
if [[ ${#missing[@]} -gt 0 ]]; then
    echo
    echo "Installing ${#missing[@]} package(s): ${missing[*]}"
    brew install "${missing[@]}"
fi

echo
echo "=== Installation complete ==="
echo "You may need to restart your terminal or run 'source ~/.zshrc' for changes to take effect."