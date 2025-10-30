import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv, dotenv_values
import yaml
from .config import PROFILES_DIR, get_current_profile

class EnvManager:
    def __init__(self, profile: Optional[str] = None):
        self.profile = profile or get_current_profile()
        self.profile_file = PROFILES_DIR / f"{self.profile}.json"

    def load_env(self) -> Dict[str, str]:
        """Load environment variables from profile."""
        if not self.profile_file.exists():
            return {}

        # Read file content
        with open(self.profile_file, 'rb') as f:
            content = f.read()

        # Try to decode as plain JSON first
        try:
            data = json.loads(content.decode('utf-8'))
            return data
        except (json.JSONDecodeError, UnicodeDecodeError):
            # File might be encrypted, try decryption
            try:
                import tempfile
                import os
                from .encryption import decrypt_file

                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                    temp_path = temp_file.name

                try:
                    # Copy encrypted content to temp file for decryption
                    with open(temp_path, 'wb') as f:
                        f.write(content)

                    # Decrypt in place
                    decrypt_file(temp_path)

                    # Load decrypted content
                    with open(temp_path, 'r') as f:
                        data = json.load(f)

                    return data
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            except Exception:
                # If decryption fails, return empty dict
                return {}

    def save_env(self, env_vars: Dict[str, str]):
        """Save environment variables to profile."""
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        # Use binary mode to handle encrypted files later
        with open(self.profile_file, 'wb') as f:
            json_data = json.dumps(env_vars, indent=2)
            f.write(json_data.encode('utf-8'))

    def list_env(self, mask: bool = True) -> Dict[str, str]:
        """List all environment variables."""
        env_vars = self.load_env()
        if mask:
            # Simple masking for keys containing 'secret', 'key', 'token', 'password'
            masked = {}
            for k, v in env_vars.items():
                if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']):
                    masked[k] = '*' * len(v)
                else:
                    masked[k] = v
            return masked
        return env_vars

    def add_env(self, key: str, value: str):
        """Add or update an environment variable."""
        env_vars = self.load_env()
        env_vars[key] = value
        self.save_env(env_vars)

    def remove_env(self, key: str):
        """Remove an environment variable."""
        env_vars = self.load_env()
        if key in env_vars:
            del env_vars[key]
            self.save_env(env_vars)

    def load_from_file(self, file_path: str, format: str = "env"):
        """Load environment variables from a file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found")

        if format == "env":
            env_vars = dotenv_values(path)
        elif format == "json":
            with open(path, 'r') as f:
                env_vars = json.load(f)
        elif format == "yaml":
            with open(path, 'r') as f:
                env_vars = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Filter out None values
        env_vars = {k: v for k, v in env_vars.items() if v is not None}
        self.save_env(env_vars)

    def export_to_file(self, file_path: str, format: str = "env"):
        """Export environment variables to a file."""
        env_vars = self.load_env()
        path = Path(file_path)

        if format == "env":
            with open(path, 'w') as f:
                for k, v in env_vars.items():
                    f.write(f"{k}={v}\n")
        elif format == "json":
            with open(path, 'w') as f:
                json.dump(env_vars, f, indent=2)
        elif format == "yaml":
            with open(path, 'w') as f:
                yaml.dump(env_vars, f)
        elif format == "shell":
            with open(path, 'w') as f:
                for k, v in env_vars.items():
                    f.write(f"export {k}=\"{v}\"\n")
        else:
            raise ValueError(f"Unsupported format: {format}")

    def diff(self, other_profile: str) -> Dict[str, Dict[str, str]]:
        """Compare this profile with another."""
        self_env = self.load_env()
        other_manager = EnvManager(other_profile)
        other_env = other_manager.load_env()

        added = {k: v for k, v in other_env.items() if k not in self_env}
        removed = {k: v for k, v in self_env.items() if k not in other_env}
        changed = {k: {"old": self_env[k], "new": other_env[k]} for k in self_env if k in other_env and self_env[k] != other_env[k]}

        return {"added": added, "removed": removed, "changed": changed}
