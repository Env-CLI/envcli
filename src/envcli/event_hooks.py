"""
Event-driven hooks for EnvCLI.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import httpx
from .config import CONFIG_DIR

EVENT_CONFIG_FILE = CONFIG_DIR / "event_hooks.json"

class EventHookManager:
    """Manage event-driven hooks."""

    def __init__(self):
        self.hooks: Dict[str, List[Dict]] = {}
        self.load_hooks()

    def load_hooks(self):
        """Load event hooks from config."""
        if EVENT_CONFIG_FILE.exists():
            with open(EVENT_CONFIG_FILE, 'r') as f:
                self.hooks = json.load(f)
        else:
            self.hooks = {
                "env_changed": [],
                "profile_created": [],
                "profile_deleted": [],
                "sync_completed": [],
                "validation_failed": []
            }

    def save_hooks(self):
        """Save event hooks to config."""
        EVENT_CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(EVENT_CONFIG_FILE, 'w') as f:
            json.dump(self.hooks, f, indent=2)

    def add_hook(self, event: str, hook_type: str, config: Dict) -> str:
        """Add an event hook."""
        if event not in self.hooks:
            self.hooks[event] = []

        hook = {
            "type": hook_type,
            "config": config,
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }

        self.hooks[event].append(hook)
        self.save_hooks()

        return f"Hook added for event '{event}'"

    def remove_hook(self, event: str, index: int) -> str:
        """Remove an event hook."""
        if event in self.hooks and 0 <= index < len(self.hooks[event]):
            self.hooks[event].pop(index)
            self.save_hooks()
            return f"Hook removed from event '{event}'"
        return "Hook not found"

    def trigger_event(self, event: str, data: Dict = None) -> List[str]:
        """Trigger all hooks for an event."""
        results = []

        if event not in self.hooks:
            return results

        for hook in self.hooks[event]:
            if not hook.get("enabled", True):
                continue

            try:
                if hook["type"] == "webhook":
                    result = self._execute_webhook(hook["config"], data)
                elif hook["type"] == "script":
                    result = self._execute_script(hook["config"], data)
                elif hook["type"] == "command":
                    result = self._execute_command(hook["config"], data)
                else:
                    result = f"Unknown hook type: {hook['type']}"

                results.append(result)
            except Exception as e:
                results.append(f"Hook execution failed: {e}")

        return results

    def _execute_webhook(self, config: Dict, data: Dict = None) -> str:
        """Execute a webhook."""
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        timeout = config.get("timeout", 10)

        payload = {
            "event": data.get("event") if data else "unknown",
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.request(method, url, json=payload, headers=headers)
                response.raise_for_status()
                return f"Webhook sent to {url}: {response.status_code}"
        except Exception as e:
            raise Exception(f"Webhook failed: {e}")

    def _execute_script(self, config: Dict, data: Dict = None) -> str:
        """Execute a script."""
        script_path = Path(config.get("path"))
        if not script_path.exists():
            raise Exception(f"Script not found: {script_path}")

        # Prepare environment variables
        env = dict(os.environ)
        if data:
            env["ENVCLI_EVENT"] = data.get("event", "unknown")
            env["ENVCLI_DATA"] = json.dumps(data)

        try:
            result = subprocess.run(
                [str(script_path)],
                env=env,
                capture_output=True,
                text=True,
                timeout=config.get("timeout", 30)
            )

            if result.returncode == 0:
                return f"Script executed: {script_path}"
            else:
                raise Exception(f"Script failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise Exception(f"Script timeout: {script_path}")

    def _execute_command(self, config: Dict, data: Dict = None) -> str:
        """Execute a shell command."""
        command = config.get("command")
        if not command:
            raise Exception("No command specified")

        # Prepare environment variables
        env = dict(os.environ)
        if data:
            env["ENVCLI_EVENT"] = data.get("event", "unknown")
            env["ENVCLI_DATA"] = json.dumps(data)

        try:
            result = subprocess.run(
                command,
                shell=True,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.get("timeout", 30)
            )

            if result.returncode == 0:
                return f"Command executed: {command}"
            else:
                raise Exception(f"Command failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise Exception(f"Command timeout: {command}")

    def list_hooks(self, event: Optional[str] = None) -> Dict[str, List[Dict]]:
        """List all hooks or hooks for a specific event."""
        if event:
            return {event: self.hooks.get(event, [])}
        return self.hooks

# Global event hook manager
event_manager = EventHookManager()

# Event trigger functions
def trigger_env_changed(profile: str, changes: Dict):
    """Trigger environment changed event."""
    data = {
        "event": "env_changed",
        "profile": profile,
        "changes": changes,
        "timestamp": datetime.now().isoformat()
    }
    return event_manager.trigger_event("env_changed", data)

def trigger_profile_created(profile: str):
    """Trigger profile created event."""
    data = {
        "event": "profile_created",
        "profile": profile,
        "timestamp": datetime.now().isoformat()
    }
    return event_manager.trigger_event("profile_created", data)

def trigger_sync_completed(service: str, profile: str, success: bool):
    """Trigger sync completed event."""
    data = {
        "event": "sync_completed",
        "service": service,
        "profile": profile,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    return event_manager.trigger_event("sync_completed", data)

def trigger_validation_failed(profile: str, errors: List[str]):
    """Trigger validation failed event."""
    data = {
        "event": "validation_failed",
        "profile": profile,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    return event_manager.trigger_event("validation_failed", data)
