import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Callable, Any
from .config import CONFIG_DIR

PLUGINS_DIR = CONFIG_DIR / "plugins"

class PluginManager:
    """Simple plugin manager for EnvCLI."""

    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.commands: Dict[str, Callable] = {}
        PLUGINS_DIR.mkdir(exist_ok=True)

    def load_plugins(self):
        """Load all installed plugins."""
        for plugin_file in PLUGINS_DIR.glob("*.py"):
            self._load_plugin(plugin_file)

    def _load_plugin(self, plugin_path: Path):
        """Load a single plugin."""
        try:
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                plugin_name = plugin_path.stem
                self.plugins[plugin_name] = module

                # Register commands if they exist
                if hasattr(module, 'register_commands'):
                    commands = module.register_commands()
                    for cmd_name, cmd_func in commands.items():
                        self.commands[cmd_name] = cmd_func

                print(f"Loaded plugin: {plugin_name}")

        except Exception as e:
            print(f"Failed to load plugin {plugin_path}: {e}")

    def get_command(self, name: str) -> Callable:
        """Get a command from loaded plugins."""
        return self.commands.get(name)

    def list_plugins(self) -> List[str]:
        """List loaded plugins."""
        return list(self.plugins.keys())

    def install_plugin(self, plugin_path: str):
        """Install a plugin from file path."""
        source_path = Path(plugin_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        dest_path = PLUGINS_DIR / source_path.name
        dest_path.write_text(source_path.read_text())
        print(f"Installed plugin: {dest_path.name}")

        # Reload plugins
        self.load_plugins()

    def remove_plugin(self, plugin_name: str):
        """Remove a plugin."""
        plugin_file = PLUGINS_DIR / f"{plugin_name}.py"
        if plugin_file.exists():
            plugin_file.unlink()
            print(f"Removed plugin: {plugin_name}")

            # Remove from loaded plugins
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
        else:
            raise FileNotFoundError(f"Plugin not found: {plugin_name}")

# Global plugin manager instance
plugin_manager = PluginManager()

def register_commands():
    """Register plugin commands with the main CLI."""
    # This will be called during CLI setup
    plugin_manager.load_plugins()
    return plugin_manager.commands
