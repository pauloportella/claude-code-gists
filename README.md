# Claude Code Gists

A collection of personal hooks for Claude Code. These are my personal Claude Code hooks - use at your own risk!

## Prerequisites

Before installing these hooks, ensure you have the required dependencies:

### Required
- **Python 3.11+** - Required for `tomllib` module support used by dependency checkers
- **Claude Code** - The IDE these hooks are designed for

### Optional but Recommended
- **uv** - Modern Python package manager (10-100x faster than pip)
- **Git** - Required for git-related safety checks

### Quick Prerequisites Check
Run the prerequisites checker to verify your system is ready:
```bash
./check-prerequisites.sh
```

This script will check all requirements and provide specific installation guidance for any missing components.

### Installing uv (Recommended)
uv provides faster and more reliable Python package management:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal or source your shell profile
source ~/.bashrc  # or ~/.zshrc
```

**Why uv?**
- 10-100x faster than pip for most operations
- Better dependency resolution
- Built-in Python version management
- Works with existing pip/requirements.txt workflows
- Ensures hooks run with Python 3.11+ via `uv run --no-project`

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

- **user-prompt-hook.py** - Advanced prompt engineering for Claude Code (improv: mode only)
  - **ONLY processes prompts with `improv:` prefix** - normal prompts bypass hook to avoid lag
  - Uses Claude Sonnet v4 with --append-to-system-prompt for enhancement
  - Adds enhanced prompts as context (doesn't replace original)
  - Includes conversation history for context-aware enhancements
  - Logs all interactions to `~/.claude/hooks-using-claude/prompt_history.json`

### Notification Hooks

- **notification-handler.sh** - Handles system notifications for Claude Code events

## Installation

### Quick Installation (Recommended)

1. **Check Prerequisites**
   ```bash
   git clone git@github.com:pauloportella/claude-code-gists.git
   cd claude-code-gists
   ./check-prerequisites.sh
   ```

2. **Install Hooks**
   ```bash
   ./install.sh
   ```

3. **Configure Settings**
   Copy and customize the example configuration:
   ```bash
   cp examples/settings.json ~/.claude/settings.json
   # Edit ~/.claude/settings.json as needed
   ```

### Manual Installation

If you prefer manual installation or need to customize the process:

1. **Clone Repository**
   ```bash
   git clone git@github.com:pauloportella/claude-code-gists.git /path/to/your/location
   cd /path/to/your/location
   ```

2. Create symlinks to your Claude Code hooks directory:
   ```bash
   # Create directories
   mkdir -p ~/.claude/hooks
   mkdir -p ~/.claude/hooks-using-claude
   
   # Individual hooks
   ln -sf /path/to/claude-code-gists/hooks/command-safety-guard.py ~/.claude/hooks/
   ln -sf /path/to/claude-code-gists/hooks/dependency-checker.py ~/.claude/hooks/
   ln -sf /path/to/claude-code-gists/hooks/notification-handler.sh ~/.claude/hooks/
   ln -sf /path/to/claude-code-gists/hooks/security-audit.py ~/.claude/hooks/
   ln -sf /path/to/claude-code-gists/hooks/task-quality-analyzer.py ~/.claude/hooks/
   ln -sf /path/to/claude-code-gists/hooks/user-prompt-hook.py ~/.claude/hooks/
   
   # Dependency checkers module
   ln -sf /path/to/claude-code-gists/hooks/dependency_checkers ~/.claude/hooks/
   ```

3. **Configure Settings**
   Create or update your `~/.claude/settings.json` file (see examples below)

### Installation Verification

After installation, verify everything is working:
```bash
./check-prerequisites.sh
```

### Uninstallation

To remove the hooks:
```bash
./uninstall.sh
```

This will safely remove only the symlinks created by this project and optionally clean up empty directories.

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
**Advanced Prompt Engineering** - Enhances prompts with `improv:` prefix using Claude Sonnet v4:
- **ONLY processes prompts starting with `improv:`** - all other prompts bypass the hook
- Uses Claude Sonnet v4 with --append-to-system-prompt for intelligent enhancements
- Applies Anthropic's prompt engineering best practices
- Makes prompts more specific, clear, and actionable
- Includes conversation history for context-aware enhancements

**Why improv-only mode?**
- Eliminates lag for normal prompts
- Gives users explicit control over when to use advanced enhancement
- Allows quick commands without processing delay

**How to use:**
- `improv: help me fix the performance issue` → Enhanced with specific suggestions for profiling, benchmarking, and optimization
- `improv: refactor this code` → Enhanced with questions about design patterns, target architecture, and specific refactoring goals
- `improv: write tests` → Enhanced with test framework detection, coverage goals, and test strategy

**Features:**
- **Advanced Prompt Engineering**: Uses Claude Sonnet v4 with system prompt injection
- **Context-Aware**: Includes conversation history for better understanding
- **Quality Evaluation**: 500-entry history with `"pass"` property for tracking enhancement quality
- **Session Isolation**: Uses ~/.claude/hooks-using-claude to prevent conversation pollution
- **Zero-Lag Normal Mode**: Regular prompts bypass enhancement completely

**Evaluation Tracking:**
Each enhancement includes a `"pass"` property for quality assessment:
```json
{
  "timestamp": "2025-07-21T01:09:43.490675",
  "original_prompt": "improv: fix the bug",
  "enhanced_prompt": "Debug the issue by first checking error logs...",
  "model_used": "sonnet_v4_improv",
  "had_improv_prefix": true,
  "pass": true  // Manual evaluation: true (good), false (bad), null (unevaluated)
}
```

## Alternative Configuration (Without uv)

If you don't have uv installed or prefer not to use it, you can configure hooks to run with regular Python:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/command-safety-guard.py"
          }
        ]
      }
    ]
  }
}
```

**Note**: Ensure you have Python 3.11+ when using this approach, as the hooks require the `tomllib` module.

## Security Implications & Customization

### Understanding Hook Behavior

These hooks are designed with a **"fail-safe" philosophy**:
- **Blocking hooks** (command-safety-guard, task-quality-analyzer) will **allow** operations if the hook fails to execute
- **Warning hooks** (dependency-checker) provide information but don't block operations
- This prevents hooks from breaking your workflow if there are execution issues

### Security Considerations

**Command Safety Guard:**
- Blocks potentially destructive commands by default
- May block legitimate operations in specialized workflows
- Uses pattern matching that could have false positives

**Dependency Checker:**
- Makes network requests to check package versions
- Caches results but may slow down file operations
- Only warns about outdated dependencies, doesn't block

**Task Quality Analyzer:**
- Sends task descriptions to Claude API for analysis
- Uses isolated sessions to prevent conversation pollution
- May block tasks that are actually valid but poorly worded

### Customizing Hook Behavior

**Disable Specific Hooks:**
Remove or comment out hook configurations in `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      // {
      //   "matcher": "Task",
      //   "hooks": [{"type": "command", "command": "..."}]
      // }
    ]
  }
}
```

**Modify Safety Rules:**
Edit `hooks/command-safety-guard.py` to customize blocked commands:
```python
# Add your own rules to SYSTEM_SAFETY_RULES
SYSTEM_SAFETY_RULES = [
    # Your custom rules here
    (r'your-pattern', "Your custom message"),
]
```

**Adjust Dependency Checking:**
Modify `hooks/dependency-checker.py` to change behavior:
- Skip certain file types
- Modify version checking logic
- Change warning thresholds

### Performance Considerations

**Hook Execution Context:**
- Hooks run in separate processes for each tool use
- Network-dependent hooks (dependency-checker) may add latency
- Hooks timeout after a reasonable period to prevent hanging

**Optimization Tips:**
- Use `uv run --no-project` for faster Python startup
- Consider disabling hooks for large projects if performance is critical
- Monitor hook execution time in Claude's output

## Troubleshooting

### Common Issues

**"Python version too old" Error:**
```bash
# Check your Python version
python3 --version

# Install Python 3.11+ (macOS with Homebrew)
brew install python@3.11

# Install Python 3.11+ (Ubuntu/Debian)
sudo apt update && sudo apt install python3.11
```

**"uv not found" Warning:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal or reload shell
source ~/.bashrc  # or ~/.zshrc

# Verify installation
uv --version
```

**Hooks Not Executing:**
1. Check that symlinks exist and point to correct files:
   ```bash
   ls -la ~/.claude/hooks/
   ```

2. Verify hook files are executable:
   ```bash
   chmod +x ~/.claude/hooks/*.py
   ```

3. Test hook syntax:
   ```bash
   python3 -m py_compile ~/.claude/hooks/command-safety-guard.py
   ```

4. Check Claude settings.json syntax:
   ```bash
   python3 -c "import json; json.load(open('~/.claude/settings.json'.replace('~', '$HOME')))"
   ```

**Permission Errors:**
```bash
# Fix hook permissions
chmod +x ~/.claude/hooks/*.py
chmod +x ~/.claude/hooks/*.sh

# Fix directory permissions
chmod 755 ~/.claude/hooks/
```

**Hook Execution Failures:**
1. Check Claude's output for error messages
2. Run hooks manually to test:
   ```bash
   echo '{"tool_name": "Bash", "tool_input": {"command": "ls"}}' | python3 ~/.claude/hooks/command-safety-guard.py
   ```

3. Check Python module availability:
   ```bash
   python3 -c "import tomllib, json, sys, re"
   ```

**Network Issues (Dependency Checker):**
- Hook will fail gracefully if network is unavailable
- Check internet connection for package registry access
- Consider disabling dependency-checker for offline work

### Getting Help

1. **Run the prerequisites checker:**
   ```bash
   ./check-prerequisites.sh
   ```

2. **Check hook logs in Claude's output**

3. **Test individual hooks manually**

4. **Verify your settings.json configuration**

## Architecture Overview

### Hook Execution Flow

1. **Claude triggers tool use** (e.g., Bash command, file edit)
2. **Pre-tool hooks execute** (command-safety-guard, security-audit, task-quality-analyzer)
3. **Tool executes** (if not blocked by pre-tool hooks)
4. **Post-tool hooks execute** (dependency-checker)
5. **Results returned to Claude**

### Session Isolation

Hooks that use Claude API (task-quality-analyzer, user-prompt-hook) run in isolated sessions:
- Stored in `~/.claude/hooks-using-claude/`
- Prevents hook analysis from appearing in your project conversations
- Maintains separate conversation history for hook operations

### Fail-Safe Design

All hooks are designed to fail gracefully:
- If a hook crashes, the operation proceeds
- Network failures don't block file operations
- Syntax errors in hooks don't break Claude functionality

## Contributing

Feel free to fork and modify these hooks for your own use. Pull requests are welcome!

## Disclaimer

These are personal hooks I use for my Claude Code setup. They may block legitimate operations based on my personal preferences. Adjust as needed for your workflow.