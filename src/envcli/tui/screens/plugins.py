"""
Plugins screen for EnvCLI TUI.
"""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, DataTable, Label, Input
from textual.message import Message
from ...plugins import plugin_manager, PLUGINS_DIR
from ...config import get_current_profile


class PluginsScreen(Container):
    """Plugin management screen."""

    DEFAULT_CSS = """
    PluginsScreen {
        layout: vertical;
        height: 100%;
    }

    #plugins-header {
        dock: top;
        height: auto;
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    #plugins-content {
        height: 1fr;
    }

    .plugins-section {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    .plugins-controls {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }

    .plugins-controls Button {
        margin-right: 1;
    }

    #plugins-list {
        height: 20;
    }

    #plugins-table {
        height: 1fr;
    }

    #plugin-commands {
        height: 15;
    }

    #commands-table {
        height: 1fr;
    }

    #plugin-install {
        height: 10;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.selected_plugin = None

    def compose(self):
        """Compose the plugins screen."""
        with VerticalScroll(id="plugins-content"):
            # Header
            with Vertical(id="plugins-header"):
                yield Static("🔌 Plugin Management", classes="header-title")
                yield Static(self._get_plugins_status(), id="plugins-status")

            # Installed Plugins Section
            with Vertical(id="plugins-list", classes="plugins-section"):
                yield Static("📦 Installed Plugins", classes="section-title")
                yield DataTable(id="plugins-table", cursor_type="row")
                with Horizontal(classes="plugins-controls"):
                    yield Button("🔄 Refresh", id="refresh-plugins")
                    yield Button("🗑️ Remove Selected", id="remove-plugin")
                    yield Button("📂 Open Plugins Folder", id="open-plugins-folder")

            # Plugin Commands Section
            with Vertical(id="plugin-commands", classes="plugins-section"):
                yield Static("⚡ Available Commands", classes="section-title")
                yield DataTable(id="commands-table")
                with Horizontal(classes="plugins-controls"):
                    yield Button("🔄 Refresh Commands", id="refresh-commands")

            # Install Plugin Section
            with Vertical(id="plugin-install", classes="plugins-section"):
                yield Static("➕ Install Plugin", classes="section-title")
                with Horizontal(classes="plugins-controls"):
                    yield Label("Plugin Path:")
                    yield Input(placeholder="/path/to/plugin.py", id="plugin-path")
                    yield Button("📥 Install", id="install-plugin")
                yield Static("💡 Tip: Place .py files in the plugins folder or provide a path", classes="help-text")

    def on_mount(self):
        """Initialize the plugins screen."""
        self._setup_plugins_table()
        self._setup_commands_table()
        self._load_plugins()
        self._load_commands()

    def _get_plugins_status(self) -> str:
        """Get plugins status summary."""
        plugins = plugin_manager.list_plugins()
        commands = len(plugin_manager.commands)
        return f"Installed Plugins: {len(plugins)} | Available Commands: {commands} | Plugins Dir: {PLUGINS_DIR}"

    def _setup_plugins_table(self):
        """Setup the plugins table."""
        table = self.query_one("#plugins-table", DataTable)
        table.add_column("Plugin Name", width=30)
        table.add_column("Status", width=15)
        table.add_column("Commands", width=15)
        table.add_column("Location", width=40)

    def _setup_commands_table(self):
        """Setup the commands table."""
        table = self.query_one("#commands-table", DataTable)
        table.add_column("Command", width=30)
        table.add_column("Plugin", width=30)
        table.add_column("Status", width=15)

    def _load_plugins(self):
        """Load installed plugins into the table."""
        table = self.query_one("#plugins-table", DataTable)
        table.clear()

        plugins = plugin_manager.list_plugins()
        
        for plugin_name in plugins:
            plugin_module = plugin_manager.plugins.get(plugin_name)
            
            # Count commands from this plugin
            plugin_commands = 0
            if hasattr(plugin_module, 'register_commands'):
                try:
                    commands = plugin_module.register_commands()
                    plugin_commands = len(commands)
                except:
                    pass
            
            plugin_file = PLUGINS_DIR / f"{plugin_name}.py"
            location = str(plugin_file) if plugin_file.exists() else "Unknown"
            
            table.add_row(
                plugin_name,
                "✅ Loaded",
                str(plugin_commands),
                location
            )

    def _load_commands(self):
        """Load available commands into the table."""
        table = self.query_one("#commands-table", DataTable)
        table.clear()

        commands = plugin_manager.commands
        
        # Try to map commands back to plugins
        command_plugin_map = {}
        for plugin_name, plugin_module in plugin_manager.plugins.items():
            if hasattr(plugin_module, 'register_commands'):
                try:
                    plugin_commands = plugin_module.register_commands()
                    for cmd_name in plugin_commands.keys():
                        command_plugin_map[cmd_name] = plugin_name
                except:
                    pass
        
        for cmd_name in sorted(commands.keys()):
            plugin_name = command_plugin_map.get(cmd_name, "Unknown")
            table.add_row(
                cmd_name,
                plugin_name,
                "✅ Available"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "refresh-plugins":
            self._refresh_plugins()
        elif button_id == "remove-plugin":
            self._remove_plugin()
        elif button_id == "open-plugins-folder":
            self._open_plugins_folder()
        elif button_id == "refresh-commands":
            self._refresh_commands()
        elif button_id == "install-plugin":
            self._install_plugin()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in plugins table."""
        if event.data_table.id == "plugins-table":
            table = event.data_table
            row_key = event.row_key
            row_data = table.get_row(row_key)
            self.selected_plugin = str(row_data[0])  # Plugin name is first column

    def _refresh_plugins(self):
        """Refresh the plugins list."""
        try:
            # Reload plugins
            plugin_manager.load_plugins()
            
            # Refresh displays
            self._load_plugins()
            self._load_commands()
            
            # Update status
            status_widget = self.query_one("#plugins-status", Static)
            status_widget.update(self._get_plugins_status())
            
            self.notify("Plugins refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh plugins: {e}", severity="error")

    def _remove_plugin(self):
        """Remove the selected plugin."""
        if not self.selected_plugin:
            self.notify("Please select a plugin to remove", severity="warning")
            return
        
        try:
            plugin_manager.remove_plugin(self.selected_plugin)
            
            # Refresh displays
            self._load_plugins()
            self._load_commands()
            
            # Update status
            status_widget = self.query_one("#plugins-status", Static)
            status_widget.update(self._get_plugins_status())
            
            self.notify(f"Plugin removed: {self.selected_plugin}", severity="information")
            self.selected_plugin = None
        except Exception as e:
            self.notify(f"Failed to remove plugin: {e}", severity="error")

    def _open_plugins_folder(self):
        """Open the plugins folder in file manager."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(PLUGINS_DIR)])
            elif system == "Windows":
                subprocess.run(["explorer", str(PLUGINS_DIR)])
            else:  # Linux
                subprocess.run(["xdg-open", str(PLUGINS_DIR)])
            
            self.notify(f"Opened: {PLUGINS_DIR}", severity="information")
        except Exception as e:
            self.notify(f"Failed to open folder: {e}", severity="error")

    def _refresh_commands(self):
        """Refresh the commands list."""
        try:
            self._load_commands()
            self.notify("Commands refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh commands: {e}", severity="error")

    def _install_plugin(self):
        """Install a plugin from the provided path."""
        try:
            path_input = self.query_one("#plugin-path", Input)
            plugin_path = path_input.value.strip()
            
            if not plugin_path:
                self.notify("Please enter a plugin path", severity="warning")
                return
            
            # Install the plugin
            plugin_manager.install_plugin(plugin_path)
            
            # Refresh displays
            self._load_plugins()
            self._load_commands()
            
            # Update status
            status_widget = self.query_one("#plugins-status", Static)
            status_widget.update(self._get_plugins_status())
            
            # Clear input
            path_input.value = ""
            
            self.notify(f"Plugin installed from: {plugin_path}", severity="information")
        except FileNotFoundError as e:
            self.notify(f"Plugin file not found: {e}", severity="error")
        except Exception as e:
            self.notify(f"Failed to install plugin: {e}", severity="error")

