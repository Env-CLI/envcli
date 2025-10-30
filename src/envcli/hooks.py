import subprocess
from typing import List, Dict
from .config import list_hooks

def execute_hooks(hook_type: str, command: str):
    """Execute hooks of a specific type for a command."""
    hooks = list_hooks()
    for hook in hooks:
        if hook["type"] == hook_type and hook["command"] == command:
            try:
                subprocess.run(hook["hook_command"], shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Hook failed: {e}")
                # Continue with other hooks even if one fails
