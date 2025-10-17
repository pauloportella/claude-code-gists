#!/bin/bash

# Claude Code Gists Prerequisites Checker
# This script verifies that all requirements are met for the hooks to function properly

set -e  # Exit on any error

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source color helpers
source "$SCRIPT_DIR/lib/colors.sh"

section_header "Claude Code Gists Prerequisites Checker"

info_message "This script validates the following prerequisites:"
echo ""
print_bold "Required Components:"
echo "  • Python 3.11+ (for tomllib module support)"
echo "  • Claude Code IDE"
echo "  • Source hooks directory with valid Python scripts"
echo ""
print_bold "Optional Components:"
echo "  • uv (Python package manager - recommended for performance)"
echo "  • Git (required for git-related safety checks)"
echo "  • Claude configuration directory structure"
echo ""
print_bold "Validation Checks:"
echo "  • System requirements (Python version, tools availability)"
echo "  • Directory structure (Claude dirs, source hooks)"
echo "  • Hook files (executability, syntax validation)"
echo "  • Configuration (settings.json validity)"
echo ""
horizontal_line

# Track overall status
all_good=true

# Function to check command availability
check_command() {
    local cmd="$1"
    local description="$2"
    local required="$3"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        success_message "$description is available"
        if [[ "$cmd" == "python3" ]]; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            info_message "  Version: $version"
            
            # Check if version is 3.11 or higher
            local major=$(echo "$version" | cut -d. -f1)
            local minor=$(echo "$version" | cut -d. -f2)
            
            if [[ "$major" -gt 3 ]] || [[ "$major" -eq 3 && "$minor" -ge 11 ]]; then
                success_message "  Python version meets requirements (3.11+)"
            else
                error_message "  Python version $version is too old (requires 3.11+)"
                echo "  Reason: hooks use 'tomllib' module introduced in Python 3.11"
                if [[ "$required" == "true" ]]; then
                    all_good=false
                fi
            fi
        elif [[ "$cmd" == "uv" ]]; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            info_message "  Version: $version"
        fi
    else
        if [[ "$required" == "true" ]]; then
            error_message "$description is not available (REQUIRED)"
            all_good=false
        else
            warning_message "$description is not available (OPTIONAL)"
        fi
    fi
}

# Function to check directory structure
check_directory() {
    local dir="$1"
    local description="$2"
    local required="$3"
    
    if [[ -d "$dir" ]]; then
        success_message "$description exists"
        info_message "  Path: $dir"
    else
        if [[ "$required" == "true" ]]; then
            error_message "$description does not exist (REQUIRED)"
            all_good=false
        else
            warning_message "$description does not exist (will be created during installation)"
        fi
    fi
}

# Function to check file executability
check_hook_executable() {
    local hook_file="$1"
    local hook_name="$2"
    
    if [[ -f "$hook_file" ]]; then
        if [[ -x "$hook_file" ]]; then
            success_message "$hook_name is executable"
        else
            warning_message "$hook_name exists but is not executable"
            info_message "  Run: chmod +x $hook_file"
        fi
        
        # Test if the hook can actually run
        if python3 -m py_compile "$hook_file" 2>/dev/null; then
            success_message "$hook_name syntax is valid"
        else
            error_message "$hook_name has syntax errors"
            all_good=false
        fi
    else
        error_message "$hook_name not found at $hook_file"
        all_good=false
    fi
}

info_message "Checking system requirements..."
echo ""

# Check Python
check_command "python3" "Python 3" "true"

# Check uv (optional but recommended)
check_command "uv" "uv (Python package manager)" "false"

# Check git (for some hooks)
check_command "git" "Git" "false"

echo ""
info_message "Checking directory structure..."
echo ""

# Check Claude directories
check_directory "$HOME/.claude" "Claude configuration directory" "false"
check_directory "$HOME/.claude/hooks" "Claude hooks directory" "false"
check_directory "$HOME/.claude/hooks-using-claude" "Claude hooks session directory" "false"

# Check source hooks directory
check_directory "$SCRIPT_DIR/hooks" "Source hooks directory" "true"

echo ""
info_message "Checking hook files..."
echo ""

# Check individual hooks
HOOKS_DIR="$SCRIPT_DIR/hooks"
check_hook_executable "$HOOKS_DIR/command-safety-guard.py" "Command Safety Guard"
check_hook_executable "$HOOKS_DIR/dependency-checker.py" "Dependency Checker"
check_hook_executable "$HOOKS_DIR/security-audit.py" "Security Audit"
check_hook_executable "$HOOKS_DIR/task-quality-analyzer.py" "Task Quality Analyzer"
check_hook_executable "$HOOKS_DIR/user-prompt-hook.py" "User Prompt Hook"

# Check dependency checkers module
if [[ -d "$HOOKS_DIR/dependency_checkers" ]]; then
    success_message "Dependency checkers module exists"
    if [[ -f "$HOOKS_DIR/dependency_checkers/__init__.py" ]]; then
        success_message "Dependency checkers module is properly structured"
    else
        warning_message "Dependency checkers module missing __init__.py"
    fi
else
    error_message "Dependency checkers module not found"
    all_good=false
fi

echo ""
info_message "Checking Claude settings..."
echo ""

# Check Claude settings file
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
if [[ -f "$CLAUDE_SETTINGS" ]]; then
    success_message "Claude settings.json exists"
    
    # Check if it's valid JSON
    if python3 -c "import json; json.load(open('$CLAUDE_SETTINGS'))" 2>/dev/null; then
        success_message "Claude settings.json is valid JSON"
        
        # Check if hooks are configured
        if python3 -c "import json; data=json.load(open('$CLAUDE_SETTINGS')); exit(0 if 'hooks' in data else 1)" 2>/dev/null; then
            success_message "Hooks are configured in settings.json"
        else
            warning_message "No hooks configuration found in settings.json"
            info_message "  See examples/settings.json for reference configuration"
        fi
    else
        error_message "Claude settings.json contains invalid JSON"
        all_good=false
    fi
else
    warning_message "Claude settings.json not found"
    info_message "  You'll need to create this file to use the hooks"
    info_message "  See examples/settings.json for reference configuration"
fi

echo ""
horizontal_line

# Final status and recommendations
if [[ "$all_good" == "true" ]]; then
    echo ""
    print_green "✅ All prerequisites are met!" "true"
    echo ""
    info_message "Next steps:"
    echo "1. Run ./install.sh to create symlinks"
    echo "2. Configure ~/.claude/settings.json (see examples/settings.json)"
    echo "3. Restart Claude Code to load the hooks"
else
    echo ""
    print_red "❌ Some prerequisites are missing!" "true"
    echo ""
    error_message "Required fixes:"
    
    # Provide specific installation guidance
    if ! command -v python3 >/dev/null 2>&1; then
        echo "• Install Python 3.11+:"
        echo "  - macOS: brew install python@3.11"
        echo "  - Ubuntu/Debian: sudo apt install python3.11"
        echo "  - Windows: Download from python.org"
    else
        local version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        local major=$(echo "$version" | cut -d. -f1)
        local minor=$(echo "$version" | cut -d. -f2)
        
        if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 11 ]]; then
            echo "• Upgrade Python to 3.11+:"
            echo "  - Current version: $version"
            echo "  - macOS: brew install python@3.11"
            echo "  - Ubuntu/Debian: sudo apt install python3.11"
        fi
    fi
    
    echo ""
    warning_message "Optional improvements:"
    if ! command -v uv >/dev/null 2>&1; then
        echo "• Install uv for better performance:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "  (Restart terminal after installation)"
    fi
    
    echo ""
    info_message "After fixing issues, run this script again to verify."
fi

echo ""
