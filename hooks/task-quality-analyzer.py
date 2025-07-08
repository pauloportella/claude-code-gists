#!/usr/bin/env python3
"""
Task quality analyzer - ensures well-defined task delegation
Uses Claude to analyze task clarity, scope, and safety
"""

import json
import sys
import subprocess
import re
import os

# Enable debug logging with HOOK_DEBUG=true environment variable
DEBUG = os.environ.get('HOOK_DEBUG', '').lower() == 'true'

# Claude prompt for analyzing task quality
QUALITY_PROMPT = """Analyze this Task tool request for quality and clarity:

Description: "{description}"
Task Instructions: "{prompt}"

Evaluate:
1. Specificity: Is the task clearly defined with specific goals?
2. Scope: Is it appropriately scoped (not too broad or vague)?
3. Deliverables: Are expected outputs/results clear?
4. Security: Any requests for sensitive files or risky operations?
5. Efficiency: Should this use Task tool or simpler tools (Read, Grep, etc)?

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "quality": "good" or "poor",
  "issues": ["list", "of", "specific", "issues"] or [],
  "suggestion": "one line improvement suggestion if poor, empty string if good"
}}"""

def analyze_with_claude(description, prompt):
    """Use claude -p to analyze task quality"""
    analysis_prompt = QUALITY_PROMPT.format(
        description=description.replace('"', '\\"'),
        prompt=prompt.replace('"', '\\"')
    )
    
    try:
        # Run claude in pipe mode with timeout
        claude_path = os.path.expanduser('~/.claude/local/claude')
        result = subprocess.run(
            [claude_path, '-p', '--model', 'claude-sonnet-4-20250514'],
            input=analysis_prompt,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            
            if DEBUG:
                print(f"Claude raw output: {output}", file=sys.stderr)
            
            # First try to extract from ```json blocks
            json_block = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
            if json_block:
                try:
                    extracted = json_block.group(1)
                    if DEBUG:
                        print(f"Extracted from code block: {extracted}", file=sys.stderr)
                    return json.loads(extracted)
                except json.JSONDecodeError as e:
                    if DEBUG:
                        print(f"JSON decode error from code block: {e}", file=sys.stderr)
            
            # Fallback: try to find any JSON object
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                try:
                    extracted = json_match.group()
                    if DEBUG:
                        print(f"Extracted raw JSON: {extracted}", file=sys.stderr)
                    return json.loads(extracted)
                except json.JSONDecodeError as e:
                    if DEBUG:
                        print(f"JSON decode error from raw: {e}", file=sys.stderr)
            
            if DEBUG:
                print("No valid JSON found in output", file=sys.stderr)
        
        return None
            
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        # If analysis fails, err on the side of allowing the task
        return None

def main():
    try:
        # Read hook input from stdin
        data = json.loads(sys.stdin.read())
        tool_input = data.get('tool_input', {})
        
        description = tool_input.get('description', '').strip()
        prompt = tool_input.get('prompt', '').strip()
        
        # Quick pre-checks before calling Claude
        if not description or not prompt:
            print(json.dumps({
                "decision": "block",
                "reason": "🚫 Task requires both description and prompt"
            }))
            return
        
        # Check for obvious issues
        if len(description) < 3:
            print(json.dumps({
                "decision": "block",
                "reason": "🚫 Task description too short. Use 3-5 descriptive words."
            }))
            return
            
        if len(prompt) < 20:
            print(json.dumps({
                "decision": "block",
                "reason": "🚫 Task instructions too brief. Provide clear, specific instructions."
            }))
            return
        
        # Use Claude to analyze task quality
        analysis = analyze_with_claude(description, prompt)
        
        if analysis and analysis.get('quality') == 'poor':
            # Build block message from issues
            issues = analysis.get('issues', ['Task needs improvement'])
            suggestion = analysis.get('suggestion', '')
            
            block_message = "🚫 Task Quality Issues:\n"
            for issue in issues[:3]:  # Limit to 3 issues
                block_message += f"• {issue}\n"
            
            if suggestion:
                block_message += f"\n💡 Suggestion: {suggestion}"
            
            print(json.dumps({
                "decision": "block",
                "reason": block_message
            }))
        else:
            # Task is good or analysis failed - allow it
            print(json.dumps({}))
            
    except Exception as e:
        # On any error, allow task to proceed
        # Could log error for debugging: f"Hook error: {e}"
        print(json.dumps({}))

if __name__ == "__main__":
    main()