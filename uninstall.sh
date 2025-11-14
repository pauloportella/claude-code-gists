#!/bin/bash

# Claude Code Gists Uninstallation Script
# This script removes symlinks created by install.sh from the ~/.claude/hooks/ directory

set -e  # Exit on any error

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source color helpers
source "$SCRIPT_DIR/lib/colors.sh"

HOOKS_SOURCE_DIR="$SCRIPT_DIR/hooks"
CLAUDE_HOOKS_DIR="$HOME/.claude/hooks"
CLAUDE_HOOKS_USING_CLAUDE_DIR="$HOME/.claude/hooks-using-claude"

section_header "Claude Code Gists Uninstallation Script"

# Check if Claude hooks directory exists
if [ ! -d "$CLAUDE_HOOKS_DIR" ]; then
    warning_message "Claude hooks directory not found: $CLAUDE_HOOKS_DIR"
    echo "Nothing to uninstall."
    exit 0
fi

info_message "Removing symlinks..."
echo ""

# Track if any symlinks were removed
removed_count=0

# Remove symlinks that point to our hooks directory
for item in "$CLAUDE_HOOKS_DIR"/*; do
    # Skip if no files match the pattern
    [ ! -e "$item" ] && continue
    
    item_name=$(basename "$item")
    
    # Check if it's a symlink pointing to our hooks directory
    if [ -L "$item" ]; then
        link_target=$(readlink "$item")
        # Check if the symlink points to our hooks directory
        if [[ "$link_target" == "$HOOKS_SOURCE_DIR"* ]]; then
            warning_message "Removing symlink: $item_name"
            info_message "  Symlink path: $item -> $link_target"
            rm "$item"
            removed_count=$((removed_count + 1))
        else
            info_message "Skipping symlink (not ours): $item_name -> $link_target"
        fi
    else
        info_message "Skipping non-symlink: $item_name"
    fi
done

echo ""

if [ $removed_count -eq 0 ]; then
    warning_message "No symlinks from this project were found to remove."
else
    success_message "Successfully removed $removed_count symlink(s)."
fi

# Check if hooks directory exists and is empty and offer to remove it
if [ -d "$CLAUDE_HOOKS_DIR" ] && [ -z "$(ls -A "$CLAUDE_HOOKS_DIR")" ]; then
    echo ""
    warning_message "The ~/.claude/hooks directory is now empty."
    read -p "Would you like to remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rmdir "$CLAUDE_HOOKS_DIR"
        success_message "Removed empty hooks directory"
    fi
fi

# Check if hooks-using-claude directory exists and offer to remove it
if [ -d "$CLAUDE_HOOKS_USING_CLAUDE_DIR" ]; then
    echo ""
    warning_message "The ~/.claude/hooks-using-claude directory still exists."
    echo "This directory may contain Claude session data from hooks."
    read -p "Would you like to remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CLAUDE_HOOKS_USING_CLAUDE_DIR"
        success_message "Removed hooks-using-claude directory"
    else
        info_message "Keeping hooks-using-claude directory"
    fi
fi

# Check if parent .claude directory is empty and offer to remove it
CLAUDE_DIR="$HOME/.claude"
if [ -d "$CLAUDE_DIR" ] && [ -z "$(ls -A "$CLAUDE_DIR")" ]; then
    echo ""
    warning_message "The ~/.claude directory is now empty."
    read -p "Would you like to remove it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rmdir "$CLAUDE_DIR"
        success_message "Removed empty .claude directory"
    fi
fi

echo ""
print_green "Uninstallation completed!" "true"
echo ""
print_blue "Note: Your ~/.claude/settings.json file (if it exists) was not modified."
echo "You may want to remove hook configurations from it manually."
