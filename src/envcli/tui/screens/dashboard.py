"""
Dashboard screen for EnvCLI TUI
"""

from datetime import datetime
import os
import shutil
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Input, Label
from textual.screen import ModalScreen
from textual.message import Message
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from ...env_manager import EnvManager
from ...config import get_current_profile, list_profiles
from ...ai_assistant import AIAssistant
from ...encryption import decrypt_file
from ..themes import THEMES, ThemeManager
from ...config import CONFIG_DIR


def load_env_vars_with_decryption(profile_file: Path) -> dict:
    """Load environment variables, handling encrypted files."""
    manager = EnvManager(profile_file.stem)  # Get profile name from file stem
    return manager.load_env()
class ImportDialog(ModalScreen):
    """Modal dialog for importing profiles."""

    class ImportResult(Message):
        """Message sent when import is completed."""
        def __init__(self, success: bool, message: str):
            self.success = success
            self.message = message
            super().__init__()

    def __init__(self):
        super().__init__()
        self.import_profile_name = None
        self.import_file_path = None

    def compose(self) -> ComposeResult:
        """Compose the import dialog."""
        with Vertical():
            yield Static("📥 Import Profile", classes="dialog-title")
            
            yield Label("Select export file:")
            
            # File path input
            yield Input(
                placeholder="Enter path to export file (e.g., /path/to/envcli_profile_export.json)",
                id="import-file-input"
            )
            
            # Quick file selection buttons
            with Horizontal(classes="quick-files"):
                yield Button("📁 Browse", id="browse-files-btn", variant="default")
                yield Label("Quick files:", classes="quick-label")
            
            # Profile name input
            yield Label("Target profile name:")
            yield Input(
                placeholder="Enter target profile name (will be created if not exists)",
                id="import-profile-input"
            )
            
            # Import options
            with Horizontal(classes="import-options"):
                yield Button("🔄 Merge (add new vars, keep existing)", id="merge-vars-btn", variant="primary")
                yield Button("🔁 Replace (overwrite all vars)", id="replace-vars-btn", variant="warning")
            
            # Action buttons
            with Horizontal(classes="dialog-actions"):
                yield Button("📥 Import", id="confirm-import-btn", variant="success")
                yield Button("❌ Cancel", id="cancel-import-btn", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "browse-files-btn":
            self._browse_files()
        elif button_id == "merge-vars-btn":
            self._set_import_mode("merge")
        elif button_id == "replace-vars-btn":
            self._set_import_mode("replace")
        elif button_id == "confirm-import-btn":
            self._perform_import()
        elif button_id == "cancel-import-btn":
            self.dismiss()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "import-file-input":
            self.import_file_path = event.value
        elif event.input.id == "import-profile-input":
            self.import_profile_name = event.value
    
    def _browse_files(self) -> None:
        """Browse for export files."""
        # Check home directory for typical export files
        import os
        from pathlib import Path
        
        home_dir = Path.home()
        export_files = []
        
        # Look for common export patterns
        patterns = [
            "envcli_*_export.json",
            "envcli_export.json",
            "*.env.json"
        ]
        
        for pattern in patterns:
            export_files.extend(home_dir.glob(pattern))
        
        if export_files:
            # Show file picker dialog
            self._show_file_picker(export_files)
        else:
            self.notify("No export files found in home directory", severity="warning")
    
    def _show_file_picker(self, files: list) -> None:
        """Show file picker dialog."""
        self.app.push_screen(FilePickerModal(files))
    
    def _set_import_mode(self, mode: str) -> None:
        """Set the import mode."""
        self.import_mode = mode
        self.notify(f"Import mode set to: {mode}", severity="information")
    
    def _perform_import(self) -> None:
        """Perform the actual import."""
        try:
            if not self.import_file_path:
                self.notify("Please select a file", severity="error")
                return
            
            if not self.import_profile_name:
                self.notify("Please enter a target profile name", severity="error")
                return
            
            # Perform import
            import_result = self._import_from_file(self.import_file_path, self.import_profile_name)
            
            if import_result["success"]:
                self.dismiss()
                self.post_message(self.ImportResult(True, import_result["message"]))
            else:
                self.notify(import_result["message"], severity="error")
                
        except Exception as e:
            self.notify(f"Import failed: {e}", severity="error")
    
    def _import_from_file(self, file_path: str, profile_name: str) -> dict:
        """Import profile from file."""
        try:
            import json
            from pathlib import Path
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"success": False, "message": f"File not found: {file_path}"}
            
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate import data structure
            if "variables" not in import_data:
                return {"success": False, "message": "Invalid export file format"}
            
            # Get current variables for the target profile
            manager = EnvManager(profile_name)
            current_vars = manager.load_env() if Path.exists(manager.config_file) else {}
            
            imported_vars = import_data["variables"]
            source_profile = import_data.get("profile", "unknown")
            
            # Ask user for merge/replace mode if not already set
            merge_mode = getattr(self, 'import_mode', 'merge')
            
            if merge_mode == "replace":
                final_vars = imported_vars
                action = "replaced"
            else:  # merge
                final_vars = {**current_vars, **imported_vars}
                action = "merged"
            
            # Save the imported variables
            manager.save_env(final_vars)
            
            # Update config to switch to imported profile
            from ...config import save_config, load_config
            config = load_config()
            config["current_profile"] = profile_name
            save_config(config)
            
            new_vars_count = len(imported_vars)
            total_vars_count = len(final_vars)
            
            message = f"✅ Successfully {action} {new_vars_count} variables from '{source_profile}' to '{profile_name}' (total: {total_vars_count})"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            return {"success": False, "message": f"Import error: {e}"}


class FilePickerModal(ModalScreen):
    """Simple file picker modal."""
    
    def __init__(self, files: list):
        super().__init__()
        self.files = files

    def compose(self) -> ComposeResult:
        """Compose the file picker."""
        with Vertical():
            yield Static("📁 Select Export File", classes="dialog-title")
            
            for file_path in self.files:
                file_name = file_path.name
                yield Button(file_name, id=f"file_{hash(file_path)}", variant="default")
            
            yield Button("❌ Cancel", id="cancel-picker", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id
        
        if button_id == "cancel-picker":
            self.dismiss()
        elif button_id.startswith("file_"):
            # Extract file path from hash
            file_hash = button_id.replace("file_", "")
            for file_path in self.files:
                if hash(file_path) == int(file_hash):
                    self.dismiss()
                    # Find the parent screen (ImportDialog) and set the file path
                    try:
                        app = self.app
                        screens = app.screen._screen_stack
                        for screen in screens:
                            if isinstance(screen.screen, ImportDialog):
                                import_dialog = screen.screen
                                file_input = import_dialog.query_one("#import-file-input", Input)
                                file_input.value = str(file_path)
                                import_dialog.notify(f"Selected: {file_path.name}", severity="information")
                                break
                    except Exception as e:
                        print(f"Error setting file path: {e}")
                    break


class StatCard(Static):
    """A card displaying a statistic."""
    
    DEFAULT_CSS = """
    StatCard {
    padding: 1;
    height: 7;
    width: 1fr;
    margin: 0 1;
    }
    """
    
    def __init__(self, label: str, value: str, icon: str = "", classes: str = ""):
        super().__init__(classes=classes)
        self.label = label
        self.value = value
        self.icon = icon
        theme_manager = ThemeManager(CONFIG_DIR)
        self.theme_colors = THEMES[theme_manager.get_current_theme()]
    
    def render(self) -> Text:
        """Render the stat card."""
        text = Text()

        if self.icon:
            text.append(f"{self.icon}\n", style=f"bold {self.theme_colors.accent}")

        text.append(f"{self.value}\n", style=f"bold {self.theme_colors.success}")
        text.append(self.label, style=self.theme_colors.text_dim)

        text.justify = "center"
        return text


class AlertFeed(Static):
    """Feed of recent alerts and notifications."""

    DEFAULT_CSS = """
    AlertFeed {
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, profile: str, classes: str = ""):
        super().__init__(classes=classes)
        self.profile = profile
        theme_manager = ThemeManager(CONFIG_DIR)
        self.theme_colors = THEMES[theme_manager.get_current_theme()]

    def render(self) -> Panel:
        """Render the alert feed."""
        from ...ai_actions import AIActionExecutor

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Icon", width=3)
        table.add_column("Message")
        table.add_column("Time", width=10)

        # Get real activity data
        alerts = []

        # Check for recent AI actions
        executor = AIActionExecutor(self.profile)
        history = executor.get_action_history(limit=3)
        for entry in history:
            action = entry.get("action", {})
            timestamp = entry.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_ago = self._time_ago(dt)
                    alerts.append(("+", f"[green]{action.get('description', 'Action applied')}[/green]", time_ago))
                except:
                    pass

        # Add profile info
        manager = EnvManager(self.profile)
        env_vars = manager.load_env()
        alerts.append(("vFO", f"[blue]Profile '{self.profile}' has {len(env_vars)} variables[/blue]", "now"))

        # Check for sensitive variables
        sensitive_count = sum(1 for k in env_vars.keys()
                            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
        if sensitive_count > 0:
            alerts.append(("[", f"[yellow]{sensitive_count} sensitive variables detected[/yellow]", "now"))

        # Fill with placeholder if not enough
        if len(alerts) == 0:
            alerts.append(("vFO", "[dim]No recent activity[/dim]", ""))

        for icon, message, time in alerts[:4]:  # Show max 4
            table.add_row(icon, message, f"[dim]{time}[/dim]")

        return Panel(
        table,
        title=f"[bold {self.theme_colors.success}]Recent Activity[/bold {self.theme_colors.success}]",
        border_style=self.theme_colors.border
        )

    def _time_ago(self, dt: datetime) -> str:
        """Calculate time ago string."""
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"


class QuickActions(Static):
    """Quick action buttons."""
    
    DEFAULT_CSS = """
    QuickActions {
        background: #1A2332;
        border: solid #37474F;
        padding: 1;
        height: auto;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose quick action buttons."""
        from textual.widgets import Label
        
        yield Label("[bold #00E676]Quick Actions[/bold #00E676]")
        
        with Horizontal():
            yield Button("* Run AI Analysis", id="btn_ai_analysis")
            yield Button("~ Sync to Cloud", id="btn_cloud_sync")
            yield Button("+ Check Compliance", id="btn_compliance")


class AIInsights(Static):
    """AI-powered insights panel."""

    DEFAULT_CSS = """
    AIInsights {
    padding: 1;
    height: 1fr;
    }
    """

    def __init__(self, profile: str, classes: str = ""):
        super().__init__(classes=classes)
        self.profile = profile
        theme_manager = ThemeManager(CONFIG_DIR)
        self.theme_colors = THEMES[theme_manager.get_current_theme()]

    def render(self) -> Panel:
        """Render AI insights."""
        text = Text()

        # Get real insights
        manager = EnvManager(self.profile)
        env_vars = load_env_vars_with_decryption(manager.profile_file)

        insights = []

        # Check for sensitive variables
        sensitive_vars = [k for k in env_vars.keys()
                         if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])]
        if sensitive_vars:
            non_uppercase = [k for k in sensitive_vars if not k.isupper()]
            if non_uppercase:
                insights.append(("!", f"{len(non_uppercase)} secrets not following uppercase convention", "#FFB300"))
            else:
                insights.append(("+", f"All {len(sensitive_vars)} secrets follow naming conventions", "#00E676"))

        # Check for naming patterns
        mixed_case = [k for k in env_vars.keys() if not k.isupper() and not k.islower()]
        if mixed_case:
            insights.append(("📝", f"{len(mixed_case)} variables could use better naming", "#2196F3"))

        # Check for duplicates or similar names
        if len(env_vars) > 0:
            insights.append(("=", f"Managing {len(env_vars)} environment variables", "#64FFDA"))

        # Check AI status
        assistant = AIAssistant()
        if assistant.enabled:
            insights.append(("*", "AI analysis available - run analysis for recommendations", "#00E676"))
        else:
            insights.append(("!", "AI features disabled - enable for smart recommendations", "#FFB300"))

        # Show insights
        if not insights:
            insights.append(("vFO", "No insights available", "#757575"))

        for icon, message, color in insights[:4]:  # Show max 4
            text.append(f"{icon} ", style=color)
            text.append(f"{message}\n", style="#E0E0E0")

        return Panel(
        text,
        title=f"[bold {self.theme_colors.success}]AI Insights[/bold {self.theme_colors.success}]",
        border_style=self.theme_colors.border
        )


class DashboardScreen(Container):
    """Main dashboard screen."""

    DEFAULT_CSS = """
    DashboardScreen {
        background: #0E141B;
        padding: 1 2;
    }

    .dashboard-title {
        dock: top;
        height: 3;
        padding: 1 0;
        color: #00E676;
        text-style: bold;
    }

    .stats-row {
        height: 9;
        margin: 1 0;
    }

    .content-row {
        height: 1fr;
        margin: 1 0;
    }

    .actions-row {
        height: 5;
        margin: 1 0;
    }

    .import-export-row {
        height: 4;
        margin: 1 0;
        align: center middle;
    }

    .import-export-row Button {
        margin: 0 2;
        min-width: 20;
    }

    /* Import Dialog Styles */
    ImportDialog {
        align: center middle;
    }

    ImportDialog > Vertical {
        width: 80%;
        height: auto;
        background: #1A2332;
        border: thick #00E676;
        padding: 2;
    }

    .dialog-title {
        text-align: center;
        text-style: bold;
        color: #00E676;
        margin-bottom: 2;
    }

    .quick-files {
        align: center middle;
        margin: 1 0;
    }

    .quick-label {
        color: #757575;
        padding: 0 1;
    }

    .import-options {
        align: center middle;
        margin: 2 0;
    }

    .import-options Button {
        margin: 0 1;
    }

    .dialog-actions {
        align: center middle;
        margin-top: 2;
    }

    .dialog-actions Button {
        margin: 0 2;
        min-width: 15;
    }

    /* File Picker Modal */
    FilePickerModal {
        align: center middle;
    }

    FilePickerModal > Vertical {
        width: 50%;
        height: auto;
        background: #1A2332;
        border: thick #64FFDA;
        padding: 2;
    }

    FilePickerModal .dialog-title {
        text-align: center;
        text-style: bold;
        color: #64FFDA;
        margin-bottom: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.manager = EnvManager(self.current_profile)
        self.assistant = AIAssistant()

    def compose(self) -> ComposeResult:
        """Compose dashboard widgets."""
        yield Static("= Dashboard Overview", classes="dashboard-title")

        # Get real data
        env_vars = load_env_vars_with_decryption(self.manager.profile_file)
        total_vars = len(env_vars)
        profiles = list_profiles()
        total_profiles = len(profiles)

        # Count sensitive variables
        sensitive_count = sum(1 for k in env_vars.keys()
                            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))

        # Calculate compliance score (simple heuristic)
        compliance_score = 100
        if total_vars > 0:
            # Deduct points for issues
            if sensitive_count > 0:
                # Check if sensitive vars are uppercase
                uppercase_secrets = sum(1 for k in env_vars.keys()
                                      if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])
                                      and k.isupper())
                if uppercase_secrets < sensitive_count:
                    compliance_score -= 10

        # Stats row
        with Horizontal(classes="stats-row"):
            yield StatCard("Total Variables", str(total_vars), "T", classes="stat-card")
            yield StatCard("Active Profiles", str(total_profiles), "/", classes="stat-card")
            yield StatCard("Sensitive Vars", str(sensitive_count), "[", classes="stat-card")
            yield StatCard("Compliance Score", f"{compliance_score}%", "+", classes="stat-card")
        
        # Content row
        with Horizontal(classes="content-row"):
            with Vertical():
                yield AlertFeed(self.current_profile, classes="panel")
            with Vertical():
                yield AIInsights(self.current_profile, classes="panel")
        
        # Quick actions row
        with Horizontal(classes="actions-row"):
            yield QuickActions()
        
        # Import/Export section
        with Horizontal(classes="import-export-row"):
            yield Button("📤 Export Profile", id="btn_export", variant="primary")
            yield Button("📥 Import Profile", id="btn_import", variant="success")
            yield Button("🐚 Export to Shell RC", id="btn_export_shell", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_ai_analysis":
            # Navigate to AI Analysis screen
            from ..components.sidebar import Sidebar
            self.app.post_message(Sidebar.ModuleSelected("ai_analysis"))
        elif button_id == "btn_cloud_sync":
            # Navigate to Cloud Sync screen
            from ..components.sidebar import Sidebar
            self.app.post_message(Sidebar.ModuleSelected("cloud_sync"))
        elif button_id == "btn_compliance":
            # Navigate to Compliance screen
            from ..components.sidebar import Sidebar
            self.app.post_message(Sidebar.ModuleSelected("compliance"))
        elif button_id == "btn_export":
            self._export_profile()
        elif button_id == "btn_import":
            self._import_profile()
        elif button_id == "btn_export_shell":
            self._export_to_shell_rc()
    
    def _export_profile(self) -> None:
        """Export current profile to file."""
        try:
            import json
            from pathlib import Path
            
            env_vars = self.manager.load_env()
            export_data = {
                "profile": self.current_profile,
                "exported_at": datetime.now().isoformat(),
                "variables": env_vars
            }
            
            export_file = Path.home() / f"envcli_{self.current_profile}_export.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.notify(f"✅ Profile exported to {export_file}", severity="information")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")
            self.app.log(f"Export error: {e}")
    
    def _import_profile(self) -> None:
        """Import profile from file."""
        self.app.push_screen(ImportDialog())
    
    def on_import_dialog_import_result(self, message: ImportDialog.ImportResult) -> None:
        """Handle import completion."""
        if message.success:
            self.notify(message.message, severity="information")
            # Refresh dashboard data
            self.refresh_dashboard()
        else:
            self.notify(message.message, severity="error")
    
    def refresh_dashboard(self) -> None:
        """Refresh the dashboard content."""
        try:
            # Update profile data
            self.current_profile = get_current_profile()
            self.manager = EnvManager(self.current_profile)
            
            # Refresh the display
            # This would require rebuilding the dashboard content
            self.app.log("Dashboard refreshed after import")
        except Exception as e:
            self.app.log(f"Failed to refresh dashboard: {e}")
    
    def _export_to_shell_rc(self) -> None:
        """Export environment variables to shell RC file."""
        try:
            env_vars = load_env_vars_with_decryption(self.manager.profile_file)
            
            if not env_vars:
                self.notify("No environment variables to export", severity="warning")
                return
            
            # Create export statements
            export_lines = []
            export_lines.append(f"# Environment variables for profile: {self.current_profile}")
            export_lines.append(f"# Generated by EnvCLI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            export_lines.append("")
            
            # Sort variables for consistent output
            sorted_vars = sorted(env_vars.items())
            
            for var_name, var_value in sorted_vars:
                # Escape special characters for shell
                escaped_value = self._escape_for_shell(var_value)
                export_lines.append(f"export {var_name}={escaped_value}")
            
            export_lines.append("")
            export_lines.append("# End of EnvCLI environment variables")
            
            # Determine shell and RC file
            shell = os.environ.get('SHELL', '')
            if 'zsh' in shell:
                rc_file = Path.home() / '.zshrc'
                shell_name = 'zsh'
            elif 'bash' in shell:
                rc_file = Path.home() / '.bashrc'
                shell_name = 'bash'
            else:
                # Default to bashrc
                rc_file = Path.home() / '.bashrc'
                shell_name = 'bash'
            
            # Check if file exists and backup
            backup_file = None
            if rc_file.exists():
                backup_file = rc_file.with_suffix(f'.bashrc.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                shutil.copy2(rc_file, backup_file)
            
            # Append to RC file
            with open(rc_file, 'a') as f:
                f.write('\n' + '\n'.join(export_lines))
            
            # Provide instructions
            self.notify(f"✅ Exported {len(env_vars)} variables to {rc_file}", severity="information")
            self.notify(f"🐚 Shell: {shell_name}", severity="information")
            
            if backup_file:
                self.notify(f"📁 Backup created: {backup_file.name}", severity="information")
            
            self.notify("🔄 Run 'source ~/.bashrc' (or ~/.zshrc) to load variables", severity="information")
            
        except Exception as e:
            self.notify(f"❌ Failed to export to shell RC: {e}", severity="error")
            self.app.log(f"Shell export error: {e}")
    
    def _escape_for_shell(self, value: str) -> str:
        """Escape value for safe shell usage."""
        if not value:
            return '""'
        
        # Handle quotes and special characters
        if '"' in value:
            # Use single quotes and escape single quotes
            value = value.replace("'", "'\"'\"'")
            return f"'{value}'"
        else:
            # Use double quotes and escape special chars
            value = value.replace('\\', '\\\\')
            value = value.replace('"', '\\"')
            value = value.replace('$', '\\$')
            value = value.replace('`', '\\`')
            return f'"{value}"'

    

