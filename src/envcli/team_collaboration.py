"""
Team collaboration features for EnvCLI.
"""

import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import questionary
from .config import CONFIG_DIR
from .env_manager import EnvManager
from .encryption import get_or_create_key

TEAM_CONFIG_DIR = CONFIG_DIR / "teams"
TEAM_PROFILES_DIR = CONFIG_DIR / "team_profiles"

class TeamManager:
    """Manage team collaboration features."""

    def __init__(self):
        TEAM_CONFIG_DIR.mkdir(exist_ok=True)
        TEAM_PROFILES_DIR.mkdir(exist_ok=True)
        self.current_team: Optional[str] = None

    def create_team(self, team_name: str, admin_user: str = "admin") -> str:
        """Create a new team."""
        team_config = {
            "name": team_name,
            "created_at": datetime.now().isoformat(),
            "admin": admin_user,
            "members": [admin_user],
            "shared_profiles": [],
            "encryption_keys": {
                "current": self._generate_key(),
                "rotation_schedule": (datetime.now() + timedelta(days=90)).isoformat()
            }
        }

        team_file = TEAM_CONFIG_DIR / f"{team_name}.json"
        if team_file.exists():
            raise ValueError(f"Team '{team_name}' already exists")

        with open(team_file, 'w') as f:
            json.dump(team_config, f, indent=2)

        return f"Team '{team_name}' created successfully"

    def join_team(self, team_name: str, user: str) -> str:
        """Join an existing team."""
        team_config = self._load_team_config(team_name)
        if not team_config:
            raise ValueError(f"Team '{team_name}' not found")

        if user not in team_config["members"]:
            team_config["members"].append(user)
            self._save_team_config(team_name, team_config)

        self.current_team = team_name
        return f"Joined team '{team_name}'"

    def list_teams(self) -> List[str]:
        """List all available teams."""
        return [f.stem for f in TEAM_CONFIG_DIR.glob("*.json")]

    def create_shared_profile(self, profile_name: str, source_profile: Optional[str] = None) -> str:
        """Create a shared team profile."""
        if not self.current_team:
            raise ValueError("No active team. Join a team first.")

        team_config = self._load_team_config(self.current_team)
        if profile_name in team_config["shared_profiles"]:
            raise ValueError(f"Shared profile '{profile_name}' already exists")

        # Create the shared profile
        shared_profile_path = TEAM_PROFILES_DIR / self.current_team / f"{profile_name}.json"

        if source_profile:
            # Copy from existing profile
            manager = EnvManager(source_profile)
            env_vars = manager.load_env()
        else:
            env_vars = {}

        shared_profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(shared_profile_path, 'w') as f:
            json.dump(env_vars, f, indent=2)

        # Add to team config
        team_config["shared_profiles"].append(profile_name)
        self._save_team_config(self.current_team, team_config)

        return f"Shared profile '{profile_name}' created for team '{self.current_team}'"

    def list_shared_profiles(self) -> List[str]:
        """List shared profiles for current team."""
        if not self.current_team:
            return []

        team_config = self._load_team_config(self.current_team)
        return team_config.get("shared_profiles", [])

    def access_shared_profile(self, profile_name: str) -> EnvManager:
        """Get access to a shared team profile."""
        if not self.current_team:
            raise ValueError("No active team")

        team_config = self._load_team_config(self.current_team)
        if profile_name not in team_config["shared_profiles"]:
            raise ValueError(f"Shared profile '{profile_name}' not found")

        # Create a virtual profile manager for the shared profile
        shared_path = TEAM_PROFILES_DIR / self.current_team / f"{profile_name}.json"
        return SharedProfileManager(shared_path)

    def rotate_encryption_keys(self) -> str:
        """Rotate encryption keys for the team."""
        if not self.current_team:
            raise ValueError("No active team")

        team_config = self._load_team_config(self.current_team)

        # Generate new key
        new_key = self._generate_key()
        old_key = team_config["encryption_keys"]["current"]

        # Update config
        team_config["encryption_keys"]["previous"] = old_key
        team_config["encryption_keys"]["current"] = new_key
        team_config["encryption_keys"]["rotated_at"] = datetime.now().isoformat()
        team_config["encryption_keys"]["rotation_schedule"] = (datetime.now() + timedelta(days=90)).isoformat()

        self._save_team_config(self.current_team, team_config)

        # TODO: Re-encrypt all shared profiles with new key
        # This would require decrypting with old key and encrypting with new key

        return f"Encryption keys rotated for team '{self.current_team}'"

    def _load_team_config(self, team_name: str) -> Optional[Dict]:
        """Load team configuration."""
        team_file = TEAM_CONFIG_DIR / f"{team_name}.json"
        if team_file.exists():
            with open(team_file, 'r') as f:
                return json.load(f)
        return None

    def _save_team_config(self, team_name: str, config: Dict):
        """Save team configuration."""
        team_file = TEAM_CONFIG_DIR / f"{team_name}.json"
        with open(team_file, 'w') as f:
            json.dump(config, f, indent=2)

    def _generate_key(self) -> str:
        """Generate a secure encryption key."""
        return secrets.token_hex(32)

class SharedProfileManager(EnvManager):
    """Manager for shared team profiles."""

    def __init__(self, profile_path: Path):
        self.profile_path = profile_path
        self.profile_name = profile_path.stem

    def load_env(self) -> Dict[str, str]:
        """Load environment variables from shared profile."""
        if self.profile_path.exists():
            with open(self.profile_path, 'r') as f:
                return json.load(f)
        return {}

    def save_env(self, env_vars: Dict[str, str]):
        """Save environment variables to shared profile."""
        with open(self.profile_path, 'w') as f:
            json.dump(env_vars, f, indent=2)

# Interactive team setup
def setup_team_interactive():
    """Interactive team setup wizard."""
    team_name = questionary.text("Enter team name:").ask()
    admin_user = questionary.text("Enter your username (admin):", default="admin").ask()

    manager = TeamManager()
    result = manager.create_team(team_name, admin_user)
    print(result)

    # Ask to create initial shared profile
    create_profile = questionary.confirm("Create an initial shared profile?").ask()
    if create_profile:
        profile_name = questionary.text("Profile name:", default="shared").ask()
        result = manager.create_shared_profile(profile_name)
        print(result)

    return result
