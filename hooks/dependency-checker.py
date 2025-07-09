#!/usr/bin/env python3
# /// script
# dependencies = [
#     "tomli>=2.2.1; python_version < '3.11'",
# ]
# ///
"""
Universal Dependency Checker Hook - Verifies dependencies are up to date
Currently supports: Cargo.toml, package.json, requirements.txt, pyproject.toml, Python scripts with inline metadata
Future support: go.mod
"""

import json
import sys
import os

# Add the hooks directory to Python path so we can import from dependency_checkers
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, hooks_dir)

# Import checkers from the modular structure
try:
    from dependency_checkers import CargoChecker, NpmChecker, PipChecker
except ImportError:
    # If running from symlink, try to import using the full path
    import importlib.util
    spec = importlib.util.spec_from_file_location("dependency_checkers", os.path.join(hooks_dir, "dependency_checkers", "__init__.py"))
    dependency_checkers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dependency_checkers)
    
    CargoChecker = dependency_checkers.CargoChecker
    NpmChecker = dependency_checkers.NpmChecker
    PipChecker = dependency_checkers.PipChecker

# Registry of all checkers
CHECKERS = [
    CargoChecker(),
    NpmChecker(),
    PipChecker(),
]

def get_checker(file_path):
    """Get appropriate checker for file type"""
    for checker in CHECKERS:
        if checker.can_handle(file_path):
            return checker
    return None

def format_outdated_report(file_path, outdated_deps):
    """Format a report of outdated dependencies"""
    if not outdated_deps:
        return None
    
    lines = [f"❌ Found outdated dependencies in {file_path}:", ""]
    
    for dep in outdated_deps:
        # Add dependency type info for npm packages
        dep_type_info = f" ({dep['dep_type']})" if 'dep_type' in dep else ""
        
        if dep['is_major']:
            lines.append(f"{dep['name']}{dep_type_info}: {dep['current']} → {dep['latest']} (MAJOR VERSION - check breaking changes!)")
        else:
            lines.append(f"{dep['name']}{dep_type_info}: {dep['current']} → {dep['latest']}")
    
    lines.extend(["", "To fix, update the versions:"])
    
    for dep in outdated_deps:
        # Format update instructions based on file type
        if file_path.endswith('package.json'):
            # For npm, use the colon format
            update_format = f"{dep['name']}: \"{dep['latest']}\""
        elif file_path.endswith('requirements.txt'):
            # For requirements.txt, use == format
            update_format = f"{dep['name']}=={dep['latest']}"
        elif file_path.endswith('.py'):
            # For inline scripts, show the package with version
            update_format = f"{dep['name']}>={dep['latest']}"
        else:
            # For Cargo.toml and pyproject.toml, use the equals format
            update_format = f"{dep['name']} = \"{dep['latest']}\""
        
        if dep['is_major']:
            lines.append(f"- Update to {update_format} (review {dep['url']})")
        else:
            lines.append(f"- Update to {update_format}")
    
    return "\n".join(lines)

def main():
    try:
        # Read JSON input from stdin
        hook_input = json.loads(sys.stdin.read())
        
        # Extract file path
        file_path = hook_input.get('tool_input', {}).get('file_path', '')
        
        # For MultiEdit, check all file paths
        if not file_path:
            edits = hook_input.get('tool_input', {}).get('edits', [])
            for edit in edits:
                edit_path = edit.get('file_path', '')
                if get_checker(edit_path):
                    file_path = edit_path
                    break
        
        # Get checker for this file type
        checker = get_checker(file_path)
        if not checker:
            print(json.dumps({}))
            return
        
        # Get the new content from the tool input
        new_content = ""
        tool_name = hook_input.get('tool_name', '')
        
        if tool_name == 'Write':
            new_content = hook_input.get('tool_input', {}).get('content', '')
        elif tool_name == 'Edit':
            new_content = hook_input.get('tool_input', {}).get('new_string', '')
        elif tool_name == 'MultiEdit':
            # For MultiEdit on package.json, same issue - skip checking
            if file_path.endswith('package.json'):
                print(json.dumps({}))
                return
            # For MultiEdit, concatenate all new_strings
            edits = hook_input.get('tool_input', {}).get('edits', [])
            new_content = '\n'.join(edit.get('new_string', '') for edit in edits)
        
        if not new_content:
            print(json.dumps({}))
            return
        
        # Check dependencies
        outdated = checker.check_dependencies(file_path, new_content)
        
        # Format report
        report = format_outdated_report(file_path, outdated)
        
        if report:
            result = {
                "decision": "block",
                "reason": report
            }
            print(json.dumps(result))
        else:
            print(json.dumps({}))
            
    except Exception as e:
        # On error, allow but log to stderr
        print(f"Dependency checker error: {str(e)}", file=sys.stderr)
        print(json.dumps({}))

if __name__ == "__main__":
    main()