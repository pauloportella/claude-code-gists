#!/usr/bin/env python3
# /// script
# dependencies = [
#     "tomli>=2.2.1; python_version < '3.11'",
# ]
# ///
"""
Python dependency checker for requirements.txt, pyproject.toml, and inline script metadata (PEP 723).
"""

import re
import json
import subprocess

try:
    import tomllib
    HAS_TOML = True
except ImportError:
    try:
        # Python < 3.11
        import tomli as tomllib
        HAS_TOML = True
    except ImportError:
        # No TOML support available
        HAS_TOML = False
        tomllib = None


class PipChecker:
    """Check Python dependencies in various formats"""
    
    @staticmethod
    def can_handle(file_path):
        return (file_path.endswith('requirements.txt') or 
                file_path.endswith('pyproject.toml') or 
                file_path.endswith('.py'))
    
    @staticmethod
    def parse_version_spec(version_spec):
        """Parse Python version specifiers and extract base version"""
        version_spec = version_spec.strip()
        
        # Handle common prefixes
        for prefix in ['==', '>=', '<=', '~=', '>', '<', '!=']:
            if version_spec.startswith(prefix):
                version_spec = version_spec[len(prefix):].strip()
                break
        
        # Remove any additional constraints (e.g., "1.2.3,<2.0")
        if ',' in version_spec:
            version_spec = version_spec.split(',')[0].strip()
        
        # Extract semantic version pattern
        match = re.match(r'(\d+)(?:\.(\d+))?(?:\.(\d+))?', version_spec)
        if match:
            major = match.group(1)
            minor = match.group(2) or '0'
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
    def check_uv_available():
        """Check if uv command is available"""
        try:
            result = subprocess.run(
                ['uv', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def get_latest_version(package_name):
        """Get latest version using uv or pip"""
        # First try with uv if available
        if PipChecker.check_uv_available():
            try:
                # Use uv pip compile to get latest version
                result = subprocess.run(
                    ['uv', 'pip', 'compile', '-'],
                    input=f'{package_name}\n',
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Parse output for the package version
                    for line in result.stdout.splitlines():
                        if line.startswith(f'{package_name}=='):
                            version = line.split('==')[1].strip()
                            # Remove any comments or extras
                            if ' ' in version:
                                version = version.split(' ')[0]
                            return version
            except Exception:
                pass
        
        # Fallback to pip
        try:
            # Use pip index versions command (available in pip 21.2+)
            result = subprocess.run(
                ['pip', 'index', 'versions', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # Fallback to pip show for older pip versions
                result = subprocess.run(
                    ['pip', 'show', package_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.startswith('Version:'):
                            return line.split(':', 1)[1].strip()
                return None
            
            # Parse pip index output
            # Format: "Available versions: 1.0.0, 0.9.0, 0.8.0"
            for line in result.stdout.splitlines():
                if 'Available versions:' in line:
                    versions_str = line.split(':', 1)[1].strip()
                    versions = [v.strip() for v in versions_str.split(',')]
                    if versions:
                        return versions[0]  # First version is latest
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def extract_requirements_txt_dependencies(content):
        """Extract dependencies from requirements.txt content"""
        dependencies = []
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Skip URLs and local paths
            if any(prefix in line for prefix in ['http://', 'https://', 'git+', 'file://', '-e ', '/', '\\']):
                continue
            
            # Parse package spec
            # Handle various formats: package==1.0.0, package>=1.0.0, package[extra]>=1.0.0
            match = re.match(r'^([a-zA-Z0-9_.-]+)(?:\[[^\]]+\])?\s*([><=~!]+.*)$', line)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2)
                base_version = PipChecker.parse_version_spec(version_spec)
                if base_version:
                    dependencies.append((package_name, base_version, version_spec, 'requirements'))
        
        return dependencies
    
    @staticmethod
    def extract_pyproject_toml_dependencies(content):
        """Extract dependencies from pyproject.toml content"""
        if not HAS_TOML:
            return []
            
        dependencies = []
        
        try:
            data = tomllib.loads(content)
        except Exception:
            return []
        
        # Extract from [project] dependencies
        project = data.get('project', {})
        deps = project.get('dependencies', [])
        
        for dep in deps:
            # Skip URLs and local paths
            if any(prefix in dep for prefix in ['http://', 'https://', 'git+', 'file://', '@', '/', '\\']):
                continue
            
            # Parse dependency spec
            match = re.match(r'^([a-zA-Z0-9_.-]+)(?:\[[^\]]+\])?\s*([><=~!]+.*)$', dep)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2)
                base_version = PipChecker.parse_version_spec(version_spec)
                if base_version:
                    dependencies.append((package_name, base_version, version_spec, 'project'))
            else:
                # Handle bare package names
                match = re.match(r'^([a-zA-Z0-9_.-]+)', dep)
                if match:
                    package_name = match.group(1)
                    dependencies.append((package_name, '0.0.0', '', 'project'))
        
        # Extract from [project.optional-dependencies]
        optional_deps = project.get('optional-dependencies', {})
        for group_name, group_deps in optional_deps.items():
            for dep in group_deps:
                if any(prefix in dep for prefix in ['http://', 'https://', 'git+', 'file://', '@', '/', '\\']):
                    continue
                
                match = re.match(r'^([a-zA-Z0-9_.-]+)(?:\[[^\]]+\])?\s*([><=~!]+.*)$', dep)
                if match:
                    package_name = match.group(1)
                    version_spec = match.group(2)
                    base_version = PipChecker.parse_version_spec(version_spec)
                    if base_version:
                        dependencies.append((package_name, base_version, version_spec, f'optional[{group_name}]'))
        
        # Note: Skip [tool.uv.sources] as those are alternative sources, not versions
        
        return dependencies
    
    @staticmethod
    def extract_inline_script_dependencies(content):
        """Extract dependencies from Python script with PEP 723 inline metadata"""
        if not HAS_TOML:
            return []
            
        dependencies = []
        
        # Look for the PEP 723 metadata block
        # Format: # /// script
        #         # dependencies = ["package>=1.0.0"]
        #         # ///
        
        in_metadata_block = False
        metadata_lines = []
        
        for line in content.splitlines():
            if line.strip() == '# /// script':
                in_metadata_block = True
                continue
            elif line.strip() == '# ///' and in_metadata_block:
                break
            elif in_metadata_block and line.startswith('#'):
                # Remove the comment prefix
                metadata_lines.append(line[1:].strip())
        
        if not metadata_lines:
            return []
        
        # Parse the metadata as TOML
        metadata_content = '\n'.join(metadata_lines)
        try:
            metadata = tomllib.loads(metadata_content)
        except Exception:
            return []
        
        # Extract dependencies
        deps = metadata.get('dependencies', [])
        for dep in deps:
            # Skip URLs and local paths
            if any(prefix in dep for prefix in ['http://', 'https://', 'git+', 'file://', '@', '/', '\\']):
                continue
            
            # Parse dependency spec
            match = re.match(r'^([a-zA-Z0-9_.-]+)(?:\[[^\]]+\])?\s*([><=~!]+.*)$', dep)
            if match:
                package_name = match.group(1)
                version_spec = match.group(2)
                base_version = PipChecker.parse_version_spec(version_spec)
                if base_version:
                    dependencies.append((package_name, base_version, version_spec, 'inline'))
            else:
                # Handle bare package names
                match = re.match(r'^([a-zA-Z0-9_.-]+)', dep)
                if match:
                    package_name = match.group(1)
                    dependencies.append((package_name, '0.0.0', '', 'inline'))
        
        return dependencies
    
    @staticmethod
    def extract_dependencies(file_path, content):
        """Extract dependencies based on file type"""
        if file_path.endswith('requirements.txt'):
            return PipChecker.extract_requirements_txt_dependencies(content)
        elif file_path.endswith('pyproject.toml'):
            return PipChecker.extract_pyproject_toml_dependencies(content)
        elif file_path.endswith('.py'):
            return PipChecker.extract_inline_script_dependencies(content)
        return []
    
    @staticmethod
    def check_dependencies(file_path, content):
        """Check dependencies and return outdated ones"""
        dependencies = PipChecker.extract_dependencies(file_path, content)
        
        if not dependencies:
            return []
        
        outdated = []
        
        for package_name, current_version, version_spec, dep_type in dependencies:
            # Skip if no version was specified
            if current_version == '0.0.0':
                continue
                
            latest_version = PipChecker.get_latest_version(package_name)
            
            if not latest_version:
                continue
            
            # Only report if the latest is actually newer
            if current_version != latest_version:
                is_major = PipChecker.is_major_bump(current_version, latest_version)
                
                # Build PyPI URL
                url = f'https://pypi.org/project/{package_name}/'
                
                outdated.append({
                    'name': package_name,
                    'current': version_spec or current_version,  # Show the full spec
                    'latest': latest_version,
                    'is_major': is_major,
                    'url': url,
                    'dep_type': dep_type
                })
        
        return outdated