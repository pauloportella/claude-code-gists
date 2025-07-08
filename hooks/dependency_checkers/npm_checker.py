"""
package.json dependency checker for Node.js projects.
"""

import re
import json
import subprocess


class NpmChecker:
    """Check Node.js package.json dependencies"""
    
    @staticmethod
    def can_handle(file_path):
        return file_path.endswith('package.json')
    
    @staticmethod
    def extract_base_version(version_spec):
        """Extract base version from npm version specifiers"""
        # Remove version range prefixes
        version_spec = version_spec.strip()
        
        # Handle various npm version formats
        # ^1.2.3 -> 1.2.3
        # ~1.2.3 -> 1.2.3
        # >=1.2.3 -> 1.2.3
        # 1.2.x -> 1.2.0
        # 1.2.* -> 1.2.0
        
        # Remove common prefixes
        for prefix in ['^', '~', '>=', '>', '<=', '<', '=']:
            if version_spec.startswith(prefix):
                version_spec = version_spec[len(prefix):].strip()
        
        # Handle .x or .* endings
        if version_spec.endswith('.x') or version_spec.endswith('.*'):
            version_spec = version_spec[:-2] + '.0'
        
        # Extract semantic version pattern
        match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?', version_spec)
        if match:
            major = match.group(1)
            minor = match.group(2)
            patch = match.group(3) or '0'
            return f"{major}.{minor}.{patch}"
        
        return None
    
    @staticmethod
    def is_major_bump(current, latest):
        """Check if it's a major version bump"""
        try:
            current_parts = current.split('.')
            latest_parts = latest.split('.')
            
            current_major = int(current_parts[0])
            latest_major = int(latest_parts[0])
            
            if current_major != latest_major:
                return True
            
            # For 0.x versions, minor bumps are breaking
            if current_major == 0 and len(current_parts) > 1 and len(latest_parts) > 1:
                current_minor = int(current_parts[1])
                latest_minor = int(latest_parts[1])
                if current_minor != latest_minor:
                    return True
            
            return False
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def get_latest_version(package_name):
        """Get latest version using npm view"""
        try:
            # Handle scoped packages
            package_arg = package_name
            
            result = subprocess.run(
                ['npm', 'view', package_arg, 'version', '--json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # npm view returns JSON string with quotes
            version = result.stdout.strip().strip('"')
            
            # Validate it's a version string
            if re.match(r'^\d+\.\d+\.\d+', version):
                return version
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def extract_dependencies(content):
        """Extract dependencies from package.json content"""
        # Handle single line edits (e.g., "express": "4.17.1",)
        content = content.strip()
        if content.startswith('"') and '":' in content and not content.startswith('{'):
            # Parse single dependency line
            match = re.match(r'"([^"]+)":\s*"([^"]+)"', content)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2)
                base_version = NpmChecker.extract_base_version(version_spec)
                if base_version:
                    return [(package_name, base_version, version_spec, 'unknown')]
            return []
        
        # Handle full JSON content
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []
        
        dependencies = []
        
        # Check all dependency types
        dep_types = ['dependencies', 'devDependencies', 'peerDependencies']
        
        for dep_type in dep_types:
            deps = data.get(dep_type, {})
            for package_name, version_spec in deps.items():
                # Skip local file dependencies
                if version_spec.startswith('file:') or version_spec.startswith('link:'):
                    continue
                
                # Skip git dependencies
                if version_spec.startswith('git') or 'github.com' in version_spec:
                    continue
                
                # Skip workspace dependencies
                if version_spec == '*' or version_spec.startswith('workspace:'):
                    continue
                
                # Extract base version from version spec
                base_version = NpmChecker.extract_base_version(version_spec)
                if base_version:
                    dependencies.append((package_name, base_version, version_spec, dep_type))
        
        return dependencies
    
    @staticmethod
    def check_dependencies(file_path, content):
        """Check dependencies and return outdated ones"""
        dependencies = NpmChecker.extract_dependencies(content)
        
        if not dependencies:
            return []
        
        outdated = []
        
        for package_name, current_version, version_spec, dep_type in dependencies:
            latest_version = NpmChecker.get_latest_version(package_name)
            
            if not latest_version:
                continue
            
            # Only report if the latest is actually newer
            if current_version != latest_version:
                # Check if latest version satisfies the current spec
                # For now, we'll report all updates
                is_major = NpmChecker.is_major_bump(current_version, latest_version)
                
                # Build npm package URL
                if package_name.startswith('@'):
                    # Scoped package
                    url_name = package_name.replace('@', '').replace('/', '%2F')
                    url = f'https://www.npmjs.com/package/{package_name}'
                else:
                    url = f'https://www.npmjs.com/package/{package_name}'
                
                outdated.append({
                    'name': package_name,
                    'current': version_spec,  # Show the full spec from package.json
                    'latest': latest_version,
                    'is_major': is_major,
                    'url': url,
                    'dep_type': dep_type
                })
        
        return outdated