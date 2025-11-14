#!/usr/bin/env python3
"""
Block access to sensitive files and system paths
"""
import json
import sys
import os

# Sensitive paths to block completely
BLOCKED_PATHS = [
    # User secrets (note: .ssh/ removed - we block specific private keys instead)
    '.aws/',
    '.gnupg/',
    '.password-store/',
    
    # System paths
    '/etc/passwd',
    '/etc/shadow',
    '/etc/sudoers',
    '/private/',
    '/System/',
    '/Library/Keychains/',
    
    # Common secret files
    '.env',
    'id_rsa',
    'id_dsa',
    'id_ecdsa',
    'id_ed25519',
    '.pem',
    '.key',
    '.p12',
    '.pfx',
    
    # Cloud credentials
    'credentials.json',
    'service-account.json',
    '.boto',
    'kubeconfig',
]

def is_sensitive_path(file_path):
    """Check if path should be blocked"""
    path = os.path.normpath(file_path).lower()
    
    for blocked in BLOCKED_PATHS:
        blocked_lower = blocked.lower()
        # Check if path contains or ends with blocked pattern
        if blocked_lower in path or path.endswith(blocked_lower.rstrip('/')):
            return True
    
    return False

def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get('tool_name', '')
        
        # Only check Read/Write operations
        if tool_name not in ['Read', 'Write']:
            print(json.dumps({}))
            sys.exit(0)
        
        file_path = input_data.get('tool_input', {}).get('file_path', '')
        
        if is_sensitive_path(file_path):
            print(json.dumps({
                "decision": "block",
                "reason": f"🚫 Access denied: '{file_path}' contains sensitive data"
            }))
        else:
            print(json.dumps({}))
            
    except:
        print(json.dumps({}))

if __name__ == "__main__":
    main()