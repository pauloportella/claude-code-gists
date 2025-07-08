# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This repository contains a collection of Python-based hooks for Claude Code that enhance safety, security, and code quality. The hooks follow a modular architecture:

1. **Hook Scripts** (`hooks/` directory):
   - Each hook is a standalone Python script (#!/usr/bin/env python3)
   - Hooks communicate via stdin/stdout with Claude Code
   - Exit code 0 = allow operation, Exit code 2 = block operation
   - Warnings can be sent to stderr without blocking

2. **Modular Checkers** (`hooks/dependency_checkers/` module):
   - Dependency checking is modularized with a base interface
   - Each package manager (npm, cargo) has its own checker class
   - Checkers are imported by the main `dependency-checker.py` script

3. **Hook Types**:
   - **PreToolUse**: Validates operations before they execute
   - **PostToolUse**: Checks results after operations complete
   - **Notification**: Handles system notifications

## Development Commands

### Testing Hooks
```bash
# Test a hook with sample input
echo '{"tool": "Bash", "params": {"command": "rm -rf /"}}' | python3 hooks/command-safety-guard.py

# Make hook executable
chmod +x hooks/*.py
```

### Adding New Dependency Checkers
New dependency checkers should be added to `hooks/dependency_checkers/` following the existing pattern:
1. Create a new file (e.g., `pip_checker.py`)
2. Implement the checker interface with methods: `can_handle()`, `check_file()`, `get_file_patterns()`
3. Import and register in `dependency-checker.py`

## Hook Input/Output Protocol

Hooks receive JSON on stdin with structure:
```json
{
  "tool": "ToolName",
  "params": {
    "file_path": "/path/to/file",
    "content": "file content"
  }
}
```

Hooks output:
- Exit code 0: Allow operation (optional warnings to stderr)
- Exit code 2: Block operation (error message to stderr)
- JSON response on stdout (optional)

## Key Implementation Details

1. **Path Safety**: All file path checks use absolute paths
2. **Version Parsing**: NPM version ranges are properly parsed (^, ~, >=, etc.)
3. **Registry Integration**: Dependency checkers fetch latest versions from official registries
4. **Pattern Matching**: Command safety uses regex patterns with careful boundary checks
5. **Modularity**: Dependency checkers use dynamic imports to support easy extension