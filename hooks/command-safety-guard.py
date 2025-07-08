#!/usr/bin/env python3
"""
Bash command validator hook for Claude Code.
Blocks dangerous commands and provides guidance for better alternatives.

Blocking rules (exit code 2):
- System-destructive commands (rm -rf /, dd to devices, etc.)
- Permission disasters (chmod 777, etc.)
- Security risks (piping to shell, backdoors)
- Git commands with --no-verify or -n flags

Warning rules (exit code 0 with stderr):
- Using grep instead of ripgrep
- Using find -name instead of ripgrep
"""

import json
import sys
import re


# Define validation rules
# System safety rules - these MUST be blocked
SYSTEM_SAFETY_RULES = [
    # Filesystem destruction
    (r'\brm\s+(-[rfI]*\s+)*(/|/\*|~|\$HOME|/Users|/home|/var|/etc|/usr|/bin|/opt)(\s|$)', 
     "🚫 CATASTROPHIC: This would delete critical system directories!"),
    (r'\brm\s+(-[rfI]*\s+)*(\.|\.\.|\.\*)(\s|$)', 
     "🚫 DANGEROUS: This would delete current directory or all hidden files!"),
    (r'\brm\s+(-[rfI]*\s+)*\*(\s|$)', 
     "🚫 DANGEROUS: This would delete all files in current directory!"),
    (r'\bfind\s+/\s+.*-delete', 
     "🚫 CATASTROPHIC: Recursive deletion from root directory!"),
    
    # Disk operations
    (r'\b(dd|mkfs|fdisk|parted|shred)\b.*(/dev/[sh]d|/dev/nvme|/dev/disk)', 
     "🚫 BLOCKED: Direct disk operations can destroy all data!"),
    (r'\b>\s*/dev/(sd|hd|nvme)', 
     "🚫 DISK CORRUPTION: Never write directly to disk devices!"),
    
    # Permission disasters
    (r'\bchmod\s+(-R\s+)?777\b', 
     "🚫 SECURITY DISASTER: Never use 777 permissions - this makes files world-writable!"),
    (r'\bchmod\s+(-R\s+)?000\s+/(bin|usr|etc|\s|$)', 
     "🚫 SYSTEM BREAK: This would make critical system files inaccessible!"),
    (r'\bchown\s+(-R\s+)?.*/(\s|$)', 
     "🚫 OWNERSHIP DISASTER: Changing ownership of root directory breaks the system!"),
    
    # System corruption
    (r':(\(\))\{:\|:&\};:', 
     "🚫 FORK BOMB: This would crash the system by creating infinite processes!"),
    (r'\b>\s*/etc/(passwd|sudoers|shadow|group)', 
     "🚫 SYSTEM CORRUPTION: This would corrupt critical system files!"),
    
    # Remote execution
    (r'(curl|wget)\s+[^|]*\|\s*(sudo\s+)?(bash|sh|python|ruby|perl)', 
     "🚫 SECURITY RISK: Never pipe remote content to interpreters - this allows arbitrary code execution!"),
    (r'\bnc\s+-l.*(-e|>.*/(bash|sh))', 
     "🚫 BACKDOOR: This opens a network backdoor to your system!"),
    
    # Development environment destruction
    (r'\b(brew|apt|yum|dnf|pacman)\s+(remove|uninstall|purge)\s+(-[yf]|--yes|--force).*\*', 
     "🚫 PACKAGE DISASTER: This would remove all packages!"),
    (r'docker\s+system\s+prune\s+-a.*--volumes', 
     "🚫 DOCKER WIPE: This would delete all Docker data including volumes!"),
    
    # Search command restrictions
    (r'\bgrep\b(?!.*\|)', 
     "🚫 Use 'rg' (ripgrep) instead of 'grep' for better performance and features"),
    (r'\bfind\s+\S+\s+-name\b', 
     "🚫 Use 'rg --files -g pattern' or 'rg --files | rg pattern' instead of 'find -name' for better performance"),
]

# Warning rules - provide guidance but don't block
WARNING_RULES = [
    # Currently empty - all rules moved to blocking
]


def remove_quoted_strings(command):
    """Remove quoted strings to avoid false positives in command checking."""
    # Remove single-quoted strings
    cleaned = re.sub(r"'[^']*'", "", command)
    # Remove double-quoted strings
    cleaned = re.sub(r'"[^"]*"', "", cleaned)
    return cleaned


def check_system_safety(command):
    """Check command against system safety rules."""
    # Don't check quoted strings for safety rules
    cleaned_cmd = remove_quoted_strings(command)
    
    for pattern, message in SYSTEM_SAFETY_RULES:
        if re.search(pattern, cleaned_cmd, re.IGNORECASE):
            return True, message
    
    return False, ""


def check_git_no_verify(command):
    """Check if git commit command has --no-verify or -n flag."""
    if not re.search(r'\bgit\b', command):
        return False, ""
    
    cleaned_cmd = remove_quoted_strings(command)
    
    # Only check for --no-verify on commit commands
    if not re.search(r'\bgit\s+commit\b', cleaned_cmd):
        return False, ""
    
    # Check for --no-verify or -n flag
    no_verify_pattern = r'(^|\s)--no-verify($|=|\s)'
    short_n_pattern = r'(^|\s)-n($|\s)'
    
    if re.search(no_verify_pattern, cleaned_cmd) or re.search(short_n_pattern, cleaned_cmd):
        return True, "🚫 Git commit with --no-verify flag is not allowed.\nThis ensures all git hooks and verification steps are properly executed.\nPlease run the git commit without the --no-verify flag."
    
    return False, ""


def check_warnings(command):
    """Check command against warning rules and return any guidance."""
    warnings = []
    
    for pattern, message in WARNING_RULES:
        if re.search(pattern, command):
            warnings.append(message)
    
    return warnings


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract tool information
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process Bash tool calls
        if tool_name != "Bash":
            sys.exit(0)
        
        # Get the command from tool_input
        command = tool_input.get("command", "")
        
        # Check for system safety violations first (highest priority)
        is_blocked, block_message = check_system_safety(command)
        if is_blocked:
            # Block with error message (exit code 2)
            print(f"\nBLOCKED COMMAND", file=sys.stderr)
            print(f"{block_message}\n", file=sys.stderr)
            sys.exit(2)
        
        # Check for git no-verify violations
        is_blocked, block_message = check_git_no_verify(command)
        if is_blocked:
            # Block with error message (exit code 2)
            print(f"\n{block_message}\n", file=sys.stderr)
            sys.exit(2)
        
        # Check for warnings
        warnings = check_warnings(command)
        if warnings:
            # Provide guidance but don't block (exit code 0)
            print("💡 Command improvement suggestions:", file=sys.stderr)
            for warning in warnings:
                print(f"  • {warning}", file=sys.stderr)
            print("", file=sys.stderr)  # Empty line for readability
        
        # Allow the command to proceed
        sys.exit(0)
        
    except json.JSONDecodeError:
        # If JSON parsing fails, allow the command (fail open)
        sys.exit(0)
    except Exception as e:
        # For any other errors, allow the command (fail open)
        sys.exit(0)


if __name__ == "__main__":
    main()