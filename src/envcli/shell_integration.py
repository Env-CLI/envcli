"""
Cross-shell environment variable auto-loading.
"""

import os
import platform
from pathlib import Path
from typing import Dict, Optional
import psutil
from .env_manager import EnvManager
from .config import CONFIG_DIR, get_current_profile

class ShellIntegration:
    """Handle cross-shell environment variable loading."""

    def __init__(self):
        self.shell_type = self._detect_shell()
        self.shell_rc_files = self._get_shell_rc_files()

    def _detect_shell(self) -> str:
        """Detect the current shell type."""
        # Try to get from environment
        shell_env = os.environ.get('SHELL', '').lower()

        if 'bash' in shell_env:
            return 'bash'
        elif 'zsh' in shell_env:
            return 'zsh'
        elif 'fish' in shell_env:
            return 'fish'
        elif 'powershell' in shell_env or 'pwsh' in shell_env:
            return 'powershell'
        else:
            # Try to detect from parent process
            try:
                current_pid = os.getpid()
                parent = psutil.Process(current_pid).parent()
                cmdline = ' '.join(parent.cmdline()).lower()

                if 'bash' in cmdline:
                    return 'bash'
                elif 'zsh' in cmdline:
                    return 'zsh'
                elif 'fish' in cmdline:
                    return 'fish'
                elif 'powershell' in cmdline or 'pwsh' in cmdline:
                    return 'powershell'
            except:
                pass

        return 'bash'  # Default fallback

    def _get_shell_rc_files(self) -> Dict[str, Path]:
        """Get shell RC files for different shells."""
        home = Path.home()

        return {
            'bash': home / '.bashrc',
            'zsh': home / '.zshrc',
            'fish': home / '.config/fish/config.fish',
            'powershell': home / 'Documents/PowerShell/Microsoft.PowerShell_profile.ps1'
        }

    def generate_shell_commands(self, profile: Optional[str] = None, export_all: bool = False) -> str:
        """Generate shell commands to load environment variables."""
        profile = profile or get_current_profile()
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        commands = []
        shell = self.shell_type

        if shell in ['bash', 'zsh']:
            for key, value in env_vars.items():
                if export_all or not self._is_secret_key(key):
                    commands.append(f'export {key}="{value}"')

        elif shell == 'fish':
            for key, value in env_vars.items():
                if export_all or not self._is_secret_key(key):
                    commands.append(f'set -x {key} "{value}"')

        elif shell == 'powershell':
            for key, value in env_vars.items():
                if export_all or not self._is_secret_key(key):
                    commands.append(f'$env:{key} = "{value}"')

        return '\n'.join(commands)

    def _is_secret_key(self, key: str) -> bool:
        """Check if a key contains sensitive information."""
        secret_keywords = ['secret', 'key', 'token', 'password', 'auth', 'credential']
        return any(keyword in key.lower() for keyword in secret_keywords)

    def inject_into_shell(self, profile: Optional[str] = None, export_all: bool = False) -> str:
        """Generate commands to inject env vars into current shell."""
        return self.generate_shell_commands(profile, export_all)

    def setup_auto_loading(self, profile: Optional[str] = None, export_all: bool = False) -> str:
        """Set up auto-loading for the detected shell."""
        shell = self.shell_type
        rc_file = self.shell_rc_files.get(shell)

        if not rc_file:
            return f"Auto-loading not supported for shell: {shell}"

        commands = self.generate_shell_commands(profile, export_all)

        # Create a marker for our envcli section
        marker_start = "# >>> envcli auto-loading >>>"
        marker_end = "# <<< envcli auto-loading <<<"

        # Read existing RC file
        existing_content = ""
        if rc_file.exists():
            existing_content = rc_file.read_text()

        # Remove existing envcli section if present
        lines = existing_content.split('\n')
        new_lines = []
        in_envcli_section = False

        for line in lines:
            if line.strip() == marker_start:
                in_envcli_section = True
                continue
            elif line.strip() == marker_end:
                in_envcli_section = False
                continue
            elif not in_envcli_section:
                new_lines.append(line)

        # Add new envcli section
        new_content = '\n'.join(new_lines).rstrip() + '\n\n'
        new_content += f"{marker_start}\n"
        new_content += f"# Auto-loaded environment variables from envcli profile: {profile or get_current_profile()}\n"
        new_content += commands + '\n'
        new_content += f"{marker_end}\n"

        # Write back to RC file
        rc_file.parent.mkdir(parents=True, exist_ok=True)
        rc_file.write_text(new_content)

        return f"Auto-loading configured for {shell} in {rc_file}"

    def setup_direnv_integration(self, profile: Optional[str] = None) -> str:
        """Set up direnv integration for automatic env loading."""
        envrc_path = Path('.envrc')

        if not envrc_path.exists():
            envrc_path.touch()

        content = envrc_path.read_text()

        # Add envcli command
        envcli_command = f"envcli env load-shell {profile or get_current_profile()}"

        if envcli_command not in content:
            if content and not content.endswith('\n'):
                content += '\n'
            content += f"{envcli_command}\n"

        envrc_path.write_text(content)

        return f"Direnv integration configured in {envrc_path}"

    def load_into_current_shell(self, profile: Optional[str] = None) -> str:
        """Load environment variables into the current shell session."""
        commands = self.generate_shell_commands(profile, export_all=True)
        return f"Run these commands in your shell:\n{commands}"

def detect_shell() -> str:
    """Detect the current shell."""
    integration = ShellIntegration()
    return integration.shell_type

def setup_auto_loading(profile: Optional[str] = None, use_direnv: bool = False) -> str:
    """Set up automatic environment loading."""
    integration = ShellIntegration()

    if use_direnv:
        return integration.setup_direnv_integration(profile)
    else:
        return integration.setup_auto_loading(profile)
