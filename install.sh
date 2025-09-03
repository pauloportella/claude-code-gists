#!/bin/bash

# Claude Code Gists Installation Script
# This script creates symlinks for all hooks in the ~/.claude/hooks/ directory

set -e  # Exit on any error

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source color helpers
source "$SCRIPT_DIR/lib/colors.sh"

HOOKS_SOURCE_DIR="$SCRIPT_DIR/hooks"
CLAUDE_HOOKS_DIR="$HOME/.claude/hooks"
CLAUDE_HOOKS_USING_CLAUDE_DIR="$HOME/.claude/hooks-using-claude"

section_header "Claude Code Gists Installation Script"

# Run prerequisites check first
if [ -f "$SCRIPT_DIR/check-prerequisites.sh" ]; then
    info_message "Running prerequisites check..."
    echo ""
    
    if ! "$SCRIPT_DIR/check-prerequisites.sh"; then
        echo ""
        error_message "Prerequisites check failed!"
        echo "Please address the issues above before proceeding with installation."
        echo "You can run the prerequisites checker separately with: ./check-prerequisites.sh"
        exit 1
    fi
    
    echo ""
    info_message "Prerequisites check passed! Proceeding with installation..."
    echo ""
else
    warning_message "Prerequisites checker not found, skipping check..."
    echo ""
fi

# Check if hooks source directory exists
if [ ! -d "$HOOKS_SOURCE_DIR" ]; then
    error_message "Hooks directory not found at $HOOKS_SOURCE_DIR"
    echo "Please run this script from the root of the claude-code-gists repository."
    exit 1
fi

# Create Claude hooks directory if it doesn't exist
if [ ! -d "$CLAUDE_HOOKS_DIR" ]; then
    warning_message "Creating Claude hooks directory: $CLAUDE_HOOKS_DIR"
    mkdir -p "$CLAUDE_HOOKS_DIR"
fi

# Create isolated directory for hook Claude sessions
if [ ! -d "$CLAUDE_HOOKS_USING_CLAUDE_DIR" ]; then
    warning_message "Creating isolated directory for hook Claude sessions: $CLAUDE_HOOKS_USING_CLAUDE_DIR"
    mkdir -p "$CLAUDE_HOOKS_USING_CLAUDE_DIR"
fi

info_message "Creating symlinks..."
echo ""

# Create symlinks for all files and directories in the hooks directory
for item in "$HOOKS_SOURCE_DIR"/*; do
    # Skip if no files match the pattern
    [ ! -e "$item" ] && continue
    
    item_name=$(basename "$item")
    
    # Skip __pycache__ directories
    if [[ "$item_name" == "__pycache__" ]]; then
        continue
    fi
    
    source_path="$item"
    target_path="$CLAUDE_HOOKS_DIR/$item_name"
    
    # Remove existing symlink or file/directory if it exists
    if [ -L "$target_path" ] || [ -e "$target_path" ]; then
        warning_message "Removing existing: $target_path"
        rm -rf "$target_path"
    fi
    
    # Create symlink
    ln -sf "$source_path" "$target_path"
    
    if [ -d "$source_path" ]; then
        success_message "Created symlink: $item_name (directory)"
        info_message "  Symlink path: $target_path -> $source_path"
    else
        success_message "Created symlink: $item_name"
        info_message "  Symlink path: $target_path -> $source_path"
    fi
done

echo ""
print_green "Installation completed successfully!" "true"
echo ""
info_message "Next steps:"
echo "1. Configure your ~/.claude/settings.json file"
echo "2. See examples/settings.json for reference configuration"
echo ""
info_message "Installed hooks:"
for item in "$CLAUDE_HOOKS_DIR"/*; do
    # Skip if no files match the pattern
    [ ! -e "$item" ] && continue
    
    item_name=$(basename "$item")
    if [ -L "$item" ]; then
        if [ -d "$item" ]; then
            echo "  ✓ $item_name (directory)"
        else
            echo "  ✓ $item_name"
        fi
    fi
done

echo ""
info_message "Installation paths:"
echo "  Source: $HOOKS_SOURCE_DIR"
echo "  Target: $CLAUDE_HOOKS_DIR"
echo "  Isolated sessions: $CLAUDE_HOOKS_USING_CLAUDE_DIR"
