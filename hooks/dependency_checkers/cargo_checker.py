"""
Cargo.toml dependency checker for Rust projects.
"""

import re
import subprocess


class CargoChecker:
    """Check Rust Cargo.toml dependencies"""
    
    @staticmethod
    def can_handle(file_path):
        return file_path.endswith('Cargo.toml')
    
    @staticmethod
    def extract_version(dep_line):
        """Extract version from dependency string"""
        # Simple format: crate = "version"
        match = re.search(r'"([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[^"]+)?)"', dep_line)
        if match:
            return match.group(1)
        
        # Workspace format: { version = "x.y.z" }
        match = re.search(r'version\s*=\s*"([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[^"]+)?)"', dep_line)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def is_major_bump(current, latest):
        """Check if it's a major version bump"""
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
    
    @staticmethod
    def get_latest_version(dep_name):
        """Get latest version using cargo search"""
        try:
            result = subprocess.run(
                ['cargo', 'search', dep_name, '--limit', '1'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            for line in result.stdout.splitlines():
                if line.startswith(f"{dep_name} "):
                    match = re.search(r'"([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[^"]+)?)"', line)
                    if match:
                        return match.group(1)
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def extract_dependencies(content):
        """Extract dependencies from content"""
        dependencies = []
        
        pattern = r'^\s*([a-zA-Z0-9_-]+)\s*=\s*(\{[^}]*version[^}]*\}|"[0-9]+(?:\.[0-9]+)*)'
        
        for line in content.splitlines():
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            match = re.match(pattern, line)
            if match:
                dep_name = match.group(1)
                dep_value = line
                
                # Skip common package fields that aren't dependencies
                if dep_name in ['name', 'version', 'authors', 'edition', 'description', 
                               'license', 'repository', 'homepage', 'documentation',
                               'readme', 'keywords', 'categories', 'build', 'links',
                               'exclude', 'include', 'publish', 'metadata', 'resolver']:
                    continue
                
                # Skip workspace and path dependencies
                if 'workspace' in dep_value and 'true' in dep_value:
                    continue
                if 'path' in dep_value and '=' in dep_value:
                    continue
                
                version = CargoChecker.extract_version(dep_value)
                if version:
                    dependencies.append((dep_name, version))
        
        return dependencies
    
    @staticmethod
    def check_dependencies(file_path, content):
        """Check dependencies and return outdated ones"""
        dependencies = CargoChecker.extract_dependencies(content)
        
        if not dependencies:
            return []
        
        outdated = []
        
        for dep_name, current_version in dependencies:
            latest_version = CargoChecker.get_latest_version(dep_name)
            
            if not latest_version:
                continue
            
            if current_version != latest_version:
                is_major = CargoChecker.is_major_bump(current_version, latest_version)
                outdated.append({
                    'name': dep_name,
                    'current': current_version,
                    'latest': latest_version,
                    'is_major': is_major,
                    'url': f'https://crates.io/crates/{dep_name}/versions'
                })
        
        return outdated