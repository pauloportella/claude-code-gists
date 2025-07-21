#!/usr/bin/env python3
"""
User prompt enhancement hook - improves clarity and removes ambiguity
Uses Claude to enhance user prompts before processing
Saves enhancement history for evaluation

IMPORTANT: This hook uses ~/.claude/hooks-using-claude as the working directory
when calling Claude internally. This isolation prevents hook analysis conversations
from polluting your main project session history. The --add-dir parameter ensures
Claude still has access to your project files while keeping hook operations separate.
"""

import json
import sys
import subprocess
import re
import os
from datetime import datetime

# Enable debug logging with HOOK_DEBUG=true environment variable
DEBUG = os.environ.get('HOOK_DEBUG', '').lower() == 'true'

# Prompt for improving user prompts with improv: prefix (Sonnet)
IMPROV_PROMPT = """You are an expert prompt engineer. The user has requested prompt improvement with "improv:" prefix.

Original prompt: "{original_prompt}"

Your task:
1. Apply Anthropic's prompt engineering best practices
2. Make the prompt more specific, clear, and actionable
3. Remove ambiguity and low-value language
4. Ensure the enhanced prompt will get better results from Claude

Guidelines:
- Be specific about desired format/structure
- Add context where helpful (file paths, function names, specific technologies)
- Remove filler words and vague language
- Make instructions clear and actionable
- If the original is too vague, add reasonable assumptions
- For code requests: specify file paths, languages, frameworks, or patterns
- For debugging: ask for error messages, stack traces, and affected files
- For refactoring: identify specific functions, classes, or modules
- For new features: specify integration points and requirements

Context Analysis:
- Does this need specific file paths or directory structure?
- Should we ask for error messages or logs?
- Are there missing technical details (language, framework, version)?
- Would examples or expected output help?
- Should we specify format (markdown, code blocks, documentation)?

Return ONLY the enhanced prompt text (no explanations, no markdown, no quotes).
"""

# Prompt for contextual pre-thought enhancement (Sonnet)
NORMAL_PROMPT = """Act as contextual intelligence for Claude. Transform this user prompt into helpful guidance that includes context and suggested actions:

User prompt: "{original_prompt}"

Your task:
- Interpret the user's intent beyond just the words
- Add helpful context about what Claude should consider
- Suggest specific actions or checks Claude should perform
- Include relevant technical considerations
- Preserve the user's communication style and urgency

Examples:
- "commit and push" → "The user wants to commit and push changes. Check for unstaged files, review commit message consistency with project style, then execute git commit and push."
- "fix the bug" → "The user needs debugging assistance. Ask for error messages, reproduction steps, and affected files before proposing solutions."
- "make it faster" → "The user wants performance optimization. Identify bottlenecks, suggest specific improvements, and provide benchmark comparisons."

Return ONLY the enhanced guidance text (no explanations, no markdown, no quotes).
"""

def save_prompt_history(original, enhanced, model_used, had_improv_prefix):
    """Save prompt enhancement history to JSON file"""
    try:
        history_file = os.path.expanduser('~/.claude/hooks-using-claude/prompt_history.json')
        
        # Load existing history
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new entry with optional pass property for evaluation
        entry = {
            "timestamp": datetime.now().isoformat(),
            "original_prompt": original,
            "enhanced_prompt": enhanced,
            "model_used": model_used,
            "had_improv_prefix": had_improv_prefix,
            "pass": None  # Optional evaluation field (true/false/null)
        }
        
        history.append(entry)
        
        # Keep only last 500 entries
        if len(history) > 500:
            history = history[-500:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
        if DEBUG:
            print(f"Saved prompt history entry", file=sys.stderr)
            
    except Exception as e:
        if DEBUG:
            print(f"Failed to save prompt history: {e}", file=sys.stderr)

def get_conversation_context(transcript_path, num_messages=3):
    """Extract recent conversation context from transcript file"""
    try:
        if not transcript_path or not os.path.exists(transcript_path):
            return "No conversation history available."
        
        context_lines = []
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
            
        # Get last few messages (each line is a JSON message)
        recent_lines = lines[-num_messages*2:] if len(lines) > num_messages*2 else lines
        
        for line in recent_lines:
            try:
                msg = json.loads(line.strip())
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if content and len(content) < 200:  # Keep context concise
                    context_lines.append(f"{role}: {content}")
            except:
                continue
                
        return "\n".join(context_lines[-6:]) if context_lines else "No recent conversation context."
        
    except Exception as e:
        return f"Error reading conversation context: {e}"

def enhance_with_claude(original_prompt, use_improv=False, conversation_context=""):
    """Use Claude to enhance the user prompt"""
    # Determine model and prompt based on prefix
    if use_improv:
        model = 'claude-3-5-sonnet-20241022'
        enhancement_prompt = IMPROV_PROMPT.format(original_prompt=original_prompt.replace('"', '\\"'))
        if conversation_context:
            enhancement_prompt += f"\n\nConversation context:\n{conversation_context}"
    else:
        model = 'claude-3-5-sonnet-20241022'
        enhancement_prompt = NORMAL_PROMPT.format(original_prompt=original_prompt.replace('"', '\\"'))
        if conversation_context:
            enhancement_prompt += f"\n\nConversation context:\n{conversation_context}"
    
    try:
        # Save current directory and change to hooks isolation directory
        original_cwd = os.getcwd()
        hooks_claude_dir = os.path.expanduser('~/.claude/hooks-using-claude')
        os.chdir(hooks_claude_dir)
        
        # Run Claude in pipe mode with timeout, isolated from project sessions
        claude_path = os.path.expanduser('~/.claude/local/claude')
        result = subprocess.run(
            [claude_path, '-p', '--model', model, '--add-dir', original_cwd],
            input=enhancement_prompt,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            enhanced = result.stdout.strip()
            
            if DEBUG:
                print(f"Claude raw output: {enhanced}", file=sys.stderr)
            
            # Clean up the response - remove any markdown formatting
            enhanced = re.sub(r'^```.*\n', '', enhanced, flags=re.MULTILINE)
            enhanced = re.sub(r'\n```$', '', enhanced)
            enhanced = enhanced.strip()
            
            # Remove quotes if Claude added them
            if enhanced.startswith('"') and enhanced.endswith('"'):
                enhanced = enhanced[1:-1]
            
            return enhanced
        
        return None
            
    except (subprocess.TimeoutExpired, Exception) as e:
        if DEBUG:
            print(f"Claude enhancement failed: {e}", file=sys.stderr)
        return None
    finally:
        # Always restore original working directory
        try:
            os.chdir(original_cwd)
        except:
            pass

def main():
    try:
        # Read hook input from stdin
        raw_input = sys.stdin.read()
        data = json.loads(raw_input)
        user_prompt = data.get('prompt', '').strip()
        transcript_path = data.get('transcript_path', '')
        
        if not user_prompt:
            # No prompt to enhance
            print(json.dumps({}))
            return
        
        # Check for improv: prefix
        has_improv_prefix = user_prompt.lower().startswith('improv:')
        if has_improv_prefix:
            # Remove the prefix for processing
            clean_prompt = user_prompt[7:].strip()
        else:
            clean_prompt = user_prompt
        
        # Skip enhancement for very short prompts but still log them
        if len(clean_prompt) < 5:
            save_prompt_history(user_prompt, user_prompt, "skipped_short", has_improv_prefix)
            print(json.dumps({}))
            return
        
        # Skip enhancement if this looks like our own enhancement prompt to prevent recursion
        recursion_patterns = [
            "Improve this user prompt by removing ambiguity",
            "You are an expert prompt engineer",
            "Apply Anthropic's prompt engineering best practices", 
            "Return ONLY the enhanced prompt text",
            "Original prompt:",
            "Your task:",
            "Fix typos and improve clarity while preserving",
            "Return ONLY the improved prompt text"
        ]
        
        for pattern in recursion_patterns:
            if pattern in clean_prompt:
                # Don't log recursion attempts - just exit silently
                return
        
        # Get conversation context for better enhancement
        conversation_context = get_conversation_context(transcript_path)
        
        # Enhance the prompt with Claude
        enhanced_prompt = enhance_with_claude(clean_prompt, use_improv=has_improv_prefix, conversation_context=conversation_context)
        
        if enhanced_prompt and enhanced_prompt != clean_prompt:
            # Save to history with enhancement
            model_used = 'sonnet_improv' if has_improv_prefix else 'sonnet'
            save_prompt_history(user_prompt, enhanced_prompt, model_used, has_improv_prefix)
            
            # Add enhanced prompt as context instead of replacement
            print(f"\n[ENHANCED PROMPT]: {enhanced_prompt}")
        else:
            # Log even when no enhancement was made
            model_used = 'sonnet_improv' if has_improv_prefix else 'sonnet'
            final_prompt = enhanced_prompt if enhanced_prompt else clean_prompt
            save_prompt_history(user_prompt, final_prompt, f"{model_used}_no_change", has_improv_prefix)
            
            # No enhancement needed - no output
            
    except Exception as e:
        if DEBUG:
            print(f"Hook error: {e}", file=sys.stderr)
        # On any error, allow original prompt to proceed
        print(json.dumps({}))

if __name__ == "__main__":
    main()