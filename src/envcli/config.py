import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

CONFIG_DIR = Path.home() / ".envcli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROFILES_DIR = CONFIG_DIR / "profiles"

DEFAULT_CONFIG = {
    "default_profile": "dev",
    "remember_last_profile": True,
}

def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)
    PROFILES_DIR.mkdir(exist_ok=True)

def load_config() -> Dict[str, Any]:
    """Load global configuration."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f) or DEFAULT_CONFIG
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    """Save global configuration."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

def get_current_profile() -> str:
    """Get the current active profile."""
    config = load_config()
    return config.get("current_profile", config["default_profile"])

def set_current_profile(profile: str):
    """Set the current active profile."""
    config = load_config()
    config["current_profile"] = profile
    save_config(config)

def list_profiles() -> List[str]:
    """List all available profiles."""
    ensure_config_dir()
    profiles = []
    for file in PROFILES_DIR.glob("*.json"):
        profiles.append(file.stem)
    return sorted(profiles)

def create_profile(name: str):
    """Create a new profile."""
    ensure_config_dir()
    profile_file = PROFILES_DIR / f"{name}.json"
    if profile_file.exists():
        raise ValueError(f"Profile '{name}' already exists")
    with open(profile_file, 'w') as f:
        json.dump({}, f)

def list_hooks() -> List[Dict[str, str]]:
    """List all configured hooks."""
    config = load_config()
    return config.get("hooks", [])

def add_hook(hook_type: str, command: str, hook_command: str):
    """Add a hook."""
    config = load_config()
    if "hooks" not in config:
        config["hooks"] = []
    config["hooks"].append({
        "type": hook_type,
        "command": command,
        "hook_command": hook_command
    })
    save_config(config)

def remove_hook(index: int):
    """Remove a hook by index."""
    config = load_config()
    hooks = config.get("hooks", [])
    if 0 <= index < len(hooks):
        hooks.pop(index)
        config["hooks"] = hooks
        save_config(config)
    else:
        raise ValueError(f"Hook index {index} out of range")

def is_analytics_enabled() -> bool:
    """Check if analytics is enabled."""
    config = load_config()
    return config.get("analytics_enabled", False)

def set_analytics_enabled(enabled: bool):
    """Enable or disable analytics."""
    config = load_config()
    config["analytics_enabled"] = enabled
    save_config(config)

def log_command(command: str):
    """Log a command execution."""
    if not is_analytics_enabled():
        return

    config = load_config()
    if "command_history" not in config:
        config["command_history"] = []
    config["command_history"].append({
        "command": command,
        "timestamp": str(__import__("datetime").datetime.now())
    })
    # Keep only last 100 commands
    config["command_history"] = config["command_history"][-100:]
    save_config(config)

def get_command_stats() -> Dict[str, int]:
    """Get command usage statistics."""
    config = load_config()
    history = config.get("command_history", [])
    stats = {}
    for entry in history:
        cmd = entry["command"].split()[0] if entry["command"] else "unknown"
        stats[cmd] = stats.get(cmd, 0) + 1
    return stats
