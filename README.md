# Claude Code Gists

A collection of personal hooks for Claude Code. These are my personal Claude Code hooks - use at your own risk!

## Hooks

### Pre-Tool Use Hooks

- **command-safety-guard.py** - Validates bash commands and blocks potentially dangerous operations
- **security-audit.py** - Audits file operations for security concerns
- **task-quality-analyzer.py** - Analyzes task descriptions for clarity and completeness

### Post-Tool Use Hooks

- **dependency-checker.py** - Checks for outdated dependencies in `package.json`, `Cargo.toml`, `requirements.txt`, `pyproject.toml`, and Python scripts
  - Supports npm packages with version range parsing
  - Supports Rust crates with cargo integration
  - Supports Python packages in requirements.txt and pyproject.toml
  - Supports PEP 723 inline script metadata in .py files
  - Uses uv if available for faster Python dependency resolution
  - Blocks writes with outdated dependencies

### User Prompt Submit Hooks

- **user-prompt-hook.py** - Enhances user prompts for clarity and precision
  - `improv:` prefix → Sonnet model for advanced prompt engineering with context analysis
  - Normal prompts → Haiku model for quick improvements
  - Adds enhanced prompts as context (doesn't replace original)
  - Includes conversation history for context-aware enhancements
  - Logs all interactions to `~/.claude/hooks-using-claude/prompt_history.json`

### Notification Hooks

- **notification-handler.sh** - Handles system notifications for Claude Code events

## Installation

1. Clone this repository:
```bash
git clone git@github.com:pauloportella/claude-code-gists.git /path/to/your/location
```

2. Create symlinks to your Claude Code hooks directory:
```bash
# Individual hooks
ln -sf /path/to/claude-code-gists/hooks/command-safety-guard.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/dependency-checker.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/notification-handler.sh ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/security-audit.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/task-quality-analyzer.py ~/.claude/hooks/
ln -sf /path/to/claude-code-gists/hooks/user-prompt-hook.py ~/.claude/hooks/

# Dependency checkers module
ln -sf /path/to/claude-code-gists/hooks/dependency_checkers ~/.claude/hooks/

# Create isolated directory for hook Claude sessions
# This prevents hook analysis from polluting your project conversation history
mkdir -p ~/.claude/hooks-using-claude
```

3. Configure your `~/.claude/settings.json` file (see `examples/settings.json` for reference)

## Settings Configuration

Your `~/.claude/settings.json` should include hook configurations like:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --no-project ~/.claude/hooks/command-safety-guard.py"
          }
        ]
      },
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --no-project ~/.claude/hooks/task-quality-analyzer.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --no-project ~/.claude/hooks/dependency-checker.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run --no-project ~/.claude/hooks/user-prompt-hook.py"
          }
        ]
      }
    ]
  }
}
```

**Note**: Using `uv run --no-project` is recommended to:
- Ensure Python 3.11+ is used (required for `tomllib` support)
- Prevent conflicts with your project's dependencies
- Avoid build errors from outdated dependencies interfering with hook execution

## Hook Details

### command-safety-guard.py
Blocks dangerous bash commands including:
- System-destructive commands (rm -rf /, dd to devices)
- Permission disasters (chmod 777)
- Security risks (piping to shell, backdoors)
- Git commits with --no-verify flag
- Forces use of ripgrep over grep/find

### dependency-checker.py
Checks dependencies in:
- `package.json` - npm packages (dependencies, devDependencies, peerDependencies)
- `Cargo.toml` - Rust crates
- `requirements.txt` - Python packages with version specifiers
- `pyproject.toml` - Modern Python projects (project.dependencies and optional-dependencies)
- Python scripts (`.py`) - PEP 723 inline script metadata

Features:
- Detects outdated dependencies
- Shows current vs latest versions
- Warns about major version changes
- Provides package registry URLs (npm, crates.io, PyPI)
- Uses uv for faster Python dependency resolution when available
- Handles various version specifiers (==, >=, ~=, etc.)

### security-audit.py
Audits file operations for:
- Sensitive file access
- Security best practices
- Path traversal attempts

### task-quality-analyzer.py
Analyzes task descriptions using Claude Sonnet to ensure quality:
- Validates task clarity and completeness
- Blocks vague or poorly defined tasks
- Provides specific improvement suggestions
- Uses isolated Claude sessions via ~/.claude/hooks-using-claude
- Prevents task analysis from polluting project conversation history

Features:
- AI-powered task quality analysis
- Blocks tasks with unclear scope or deliverables
- Suggests specific improvements for rejected tasks
- Allows tasks that meet quality standards
- Falls back to allowing tasks if analysis fails

### user-prompt-hook.py
Enhances user prompts for clarity and precision using Claude:
- **improv: prefix** - Uses Sonnet model for comprehensive prompt engineering
- **Normal prompts** - Uses Haiku model for quick improvements
- Includes conversation context from transcript for intelligent enhancements
- Adds enhanced prompts as context (preserves original)
- Logs all interactions to ~/.claude/hooks-using-claude/prompt_history.json

Features:
- Context-aware prompt enhancement using conversation history
- Advanced prompt engineering for code-related tasks:
  - Adds file paths and technical specifications
  - Requests error messages and logs for debugging
  - Specifies output formats and requirements
- Prevents recursion with internal enhancement detection
- Maintains complete history for evaluation
- Uses isolated Claude sessions to avoid session pollution

## Contributing

Feel free to fork and modify these hooks for your own use. Pull requests are welcome!

## Disclaimer

These are personal hooks I use for my Claude Code setup. They may block legitimate operations based on my personal preferences. Adjust as needed for your workflow.