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
   - Each package manager (npm, cargo, pip) has its own checker class
   - Checkers are imported by the main `dependency-checker.py` script

3. **Hook Types**:
   - **PreToolUse**: Validates operations before they execute
   - **PostToolUse**: Checks results after operations complete
   - **Notification**: Handles system notifications

## Available Hooks

### Pre-Tool Use Hooks
- **command-safety-guard.py**: Validates bash commands and blocks dangerous operations (rm -rf /, chmod 777, etc.)
- **security-audit.py**: Audits file operations for security concerns and path traversal attempts  
- **task-quality-analyzer.py**: Analyzes task descriptions for clarity and completeness

### Post-Tool Use Hooks
- **dependency-checker.py**: Checks for outdated dependencies in package.json, Cargo.toml, requirements.txt, pyproject.toml, and Python scripts with PEP 723 inline metadata

### User Prompt Submit Hooks
- **user-prompt-hook.py**: Enhances user prompts for clarity and precision
  - `improv:` prefix → Sonnet model for advanced prompt engineering
  - Normal prompts → Haiku model for quick improvements
  - Completely replaces original prompts with enhanced versions
  - Logs enhancement history to `~/.claude/hooks-using-claude/prompt_history.json`

### Notification Hooks
- **notification-handler.sh**: Handles system notifications for Claude Code events

## Development Commands

### Testing Hooks
```bash
# Test individual hooks with sample input
echo '{"tool": "Bash", "params": {"command": "rm -rf /"}}' | python3 hooks/command-safety-guard.py
echo '{"tool": "Edit", "params": {"file_path": "/path/to/package.json", "content": "..."}}' | python3 hooks/dependency-checker.py
echo '{"user_prompt": "improv: fix the bug"}' | python3 hooks/user-prompt-hook.py
echo '{"user_prompt": "make this faster"}' | python3 hooks/user-prompt-hook.py

# Test all hooks
python3 hooks/command-safety-guard.py < test_input.json
python3 hooks/dependency-checker.py < test_input.json
python3 hooks/security-audit.py < test_input.json
python3 hooks/task-quality-analyzer.py < test_input.json
python3 hooks/user-prompt-hook.py < test_input.json

# Make hooks executable
chmod +x hooks/*.py
```

### Installation and Configuration
```bash
# Create symlinks to Claude Code hooks directory
ln -sf /path/to/claude-code-gists/hooks/command-safety-guard.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/dependency-checker.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/security-audit.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/task-quality-analyzer.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/user-prompt-hook.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/notification-handler.sh ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/dependency_checkers ~/.claude/hooks/

# Create isolated directory for hook Claude sessions
mkdir -p ~/.claude/hooks-using-claude
```

Reference configuration for `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/security-audit.py"}]
      },
      {
        "matcher": "Bash", 
        "hooks": [{"type": "command", "command": "~/.claude/hooks/command-safety-guard.py"}]
      },
      {
        "matcher": "Task",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/task-quality-analyzer.py"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/dependency-checker.py"}]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/user-prompt-hook.py"}]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/notification-handler.sh"}]
      }
    ]
  }
}
```

### Adding New Dependency Checkers
New dependency checkers should be added to `hooks/dependency_checkers/` following the existing pattern:
1. Create a new file (e.g., `go_checker.py`)
2. Implement the checker interface with methods: `can_handle()`, `check_dependencies()`, `extract_dependencies()`, `get_latest_version()`
3. Import and register in `dependency-checker.py`

Current checkers support:
- `npm_checker.py`: package.json files (dependencies, devDependencies, peerDependencies)
- `cargo_checker.py`: Cargo.toml files
- `pip_checker.py`: requirements.txt, pyproject.toml, and .py files with PEP 723 inline metadata

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
2. **Claude Session Isolation**: Hooks use dedicated `~/.claude/hooks-using-claude` directory
   - Prevents hook analysis from polluting project session history
   - Uses `--add-dir` to maintain project file access
   - Pattern: `cd ~/.claude/hooks-using-claude && claude --add-dir <original_pwd>`
3. **Version Parsing**: Package version ranges are properly parsed:
   - NPM: ^, ~, >=, etc.
   - Python: ==, >=, ~=, !=, <, >
   - Rust: Semantic versioning
4. **Registry Integration**: Dependency checkers fetch latest versions from official registries:
   - npm registry for Node.js packages
   - crates.io for Rust packages
   - PyPI for Python packages (using uv or pip)
5. **Pattern Matching**: Command safety uses regex patterns with careful boundary checks
6. **Modularity**: Dependency checkers use dynamic imports to support easy extension
7. **Python Support**: Handles requirements.txt, pyproject.toml, and PEP 723 inline script metadata
8. **Prompt Enhancement**: UserPromptSubmit hook completely replaces user prompts with enhanced versions

## Requirements and Best Practices

### Python Environment
- **Python 3.11+** required for `tomllib` support in dependency checkers
- **uv** recommended for faster Python dependency resolution
- Use `uv run --no-project` to avoid conflicts with project dependencies

### Hook Configuration Recommendations
- Use `uv run --no-project ~/.claude/hooks/script.py` in settings.json for Python hooks
- This ensures Python 3.11+ usage and prevents dependency conflicts
- Prevents build errors from outdated project dependencies interfering with hook execution

### Security Considerations
- Command safety guard blocks system-destructive operations
- Security audit validates file operations and path traversal attempts
- All hooks use absolute paths to prevent path-based attacks
- Hook outputs include package registry URLs for verification

## Git Commit Message Conventions

Follow these commit message patterns used in this repository:

- **Add**: For new features, functionality, or files
  - `Add Python dependency checking support`
  - `Add CLAUDE.md with hook architecture documentation`

- **Fix**: For bug fixes and vulnerability patches
  - `Fix incomplete URL substring sanitization vulnerability in npm_checker.py`

- **Improve**: For enhancements to existing features
  - `Improve pip checker single line dependency parsing and uv run usage`

### Guidelines
- Use imperative mood (Add, Fix, Improve, not Added, Fixed, Improved)
- Be specific about what was changed
- Include file names for targeted fixes
- Keep messages concise but descriptive