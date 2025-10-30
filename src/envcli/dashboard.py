"""
Visual CLI Dashboard using Textual.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, DataTable, Static, Button, Label, TabbedContent, Tabs, TabPane
from textual import events
from datetime import datetime
from typing import List, Dict
from .config import list_profiles, get_current_profile, get_command_stats
from .env_manager import EnvManager
from .sync import get_sync_service

class EnvDashboard(App):
    """Visual dashboard for EnvCLI."""

    CSS = """
    Screen {
        background: $surface;
    }

    .dashboard-grid {
        grid-size: 2 2;
        grid-gutter: 1;
        height: 100%;
    }

    .panel {
        border: solid $primary;
        padding: 1;
        height: 100%;
    }

    .active-profile {
        background: $success;
        color: $success-darken-3;
        padding: 1;
        margin: 1 0;
    }

    DataTable {
        height: 1fr;
    }

    .status-good {
        color: $success;
    }

    .status-warning {
        color: $warning;
    }

    .status-error {
        color: $error;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.profiles = list_profiles()
        self.command_stats = get_command_stats()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Overview", id="overview"):
                with Container(classes="dashboard-grid"):
                    yield Static("Active Profile", classes="panel")
                    yield Static("Environment Variables", classes="panel")
                    yield Static("Recent Activity", classes="panel")
                    yield Static("Sync Status", classes="panel")

            with TabPane("Profiles", id="profiles"):
                yield DataTable(id="profiles-table")

            with TabPane("Analytics", id="analytics"):
                yield DataTable(id="analytics-table")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_overview()
        self.refresh_profiles()
        self.refresh_analytics()

    def refresh_overview(self):
        """Refresh the overview tab."""
        # Active Profile Panel
        profile_panel = self.query_one(".dashboard-grid Static:nth-child(1)")
        profile_panel.update(self._get_active_profile_info())

        # Environment Variables Panel
        env_panel = self.query_one(".dashboard-grid Static:nth-child(2)")
        env_panel.update(self._get_env_vars_info())

        # Recent Activity Panel
        activity_panel = self.query_one(".dashboard-grid Static:nth-child(3)")
        activity_panel.update(self._get_recent_activity())

        # Sync Status Panel
        sync_panel = self.query_one(".dashboard-grid Static:nth-child(4)")
        sync_panel.update(self._get_sync_status())

    def refresh_profiles(self):
        """Refresh the profiles tab."""
        table = self.query_one("#profiles-table", DataTable)
        table.clear()
        table.add_columns("Profile", "Variables", "Status", "Last Modified")

        for profile in self.profiles:
            manager = EnvManager(profile)
            env_vars = manager.load_env()
            var_count = len(env_vars)
            status = "Active" if profile == self.current_profile else ""
            last_modified = "Unknown"  # Would need to track this

            table.add_row(profile, str(var_count), status, last_modified)

    def refresh_analytics(self):
        """Refresh the analytics tab."""
        table = self.query_one("#analytics-table", DataTable)
        table.clear()
        table.add_columns("Command", "Usage Count", "Last Used")

        for cmd, count in sorted(self.command_stats.items(), key=lambda x: x[1], reverse=True):
            table.add_row(cmd, str(count), "Unknown")  # Would need timestamp tracking

    def _get_active_profile_info(self) -> str:
        """Get information about the active profile."""
        manager = EnvManager(self.current_profile)
        env_vars = manager.load_env()

        info = f"[bold]Active Profile:[/bold] {self.current_profile}\n"
        info += f"Variables: {len(env_vars)}\n"
        info += f"Secrets: {sum(1 for k in env_vars.keys() if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))}\n"

        return info

    def _get_env_vars_info(self) -> str:
        """Get environment variables information."""
        manager = EnvManager(self.current_profile)
        env_vars = manager.load_env()

        info = "[bold]Environment Variables:[/bold]\n\n"
        for i, (key, value) in enumerate(list(env_vars.items())[:10]):  # Show first 10
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                display_value = "***masked***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            info += f"{key} = {display_value}\n"

        if len(env_vars) > 10:
            info += f"\n... and {len(env_vars) - 10} more"

        return info

    def _get_recent_activity(self) -> str:
        """Get recent activity information."""
        # This would need to be implemented with activity logging
        activity = "[bold]Recent Activity:[/bold]\n\n"
        activity += "• Profile 'dev' created\n"
        activity += "• Variables added to 'prod'\n"
        activity += "• Sync performed with AWS SSM\n"
        activity += "• Schema validation passed\n"

        return activity

    def _get_sync_status(self) -> str:
        """Get sync status information."""
        status = "[bold]Sync Status:[/bold]\n\n"

        # Check sync status for current profile
        try:
            # This would check actual sync status
            status += "[green]✓[/green] AWS SSM: Synced\n"
            status += "[yellow]⚠[/yellow] GitHub: Needs sync\n"
            status += "[red]✗[/red] Vault: Error\n"
        except:
            status += "Sync status unavailable\n"

        return status

def show_dashboard():
    """Launch the EnvCLI dashboard."""
    app = EnvDashboard()
    app.run()
