"""
Analytics screen for EnvCLI TUI.
"""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, DataTable, Label
from textual.message import Message
from ...telemetry import TelemetryAnalyzer
from ...config import get_current_profile, get_command_stats, is_analytics_enabled, set_analytics_enabled


class AnalyticsScreen(Container):
    """Analytics and usage tracking screen."""

    DEFAULT_CSS = """
    AnalyticsScreen {
        layout: vertical;
        height: 100%;
    }

    #analytics-header {
        dock: top;
        height: auto;
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    #analytics-content {
        height: 1fr;
    }

    .analytics-section {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    .analytics-controls {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }

    .analytics-controls Button {
        margin-right: 1;
    }

    #analytics-status {
        height: 8;
    }

    #command-usage {
        height: 20;
    }

    #command-table {
        height: 1fr;
    }

    #insights {
        height: 1fr;
    }

    #insights-table {
        height: 1fr;
    }
    """

    def __init__(self):
        super().__init__()
        self.analyzer = TelemetryAnalyzer()
        self.current_profile = get_current_profile()

    def compose(self):
        """Compose the analytics screen."""
        with VerticalScroll(id="analytics-content"):
            # Header
            with Vertical(id="analytics-header"):
                yield Static("📈 Analytics & Usage Tracking", classes="header-title")
                yield Static(self._get_analytics_status(), id="analytics-status-text")

            # Analytics Status Section
            with Vertical(id="analytics-status", classes="analytics-section"):
                yield Static("⚙️ Analytics Settings", classes="section-title")
                yield Static(self._get_analytics_settings(), id="analytics-settings-display")
                with Horizontal(classes="analytics-controls"):
                    yield Button("✅ Enable Analytics", id="enable-analytics")
                    yield Button("❌ Disable Analytics", id="disable-analytics")
                    yield Button("🔄 Refresh", id="refresh-analytics")

            # Command Usage Section
            with Vertical(id="command-usage", classes="analytics-section"):
                yield Static("📊 Command Usage Statistics", classes="section-title")
                yield DataTable(id="command-table")
                with Horizontal(classes="analytics-controls"):
                    yield Button("🔄 Refresh Commands", id="refresh-commands")
                    yield Button("📋 Export Stats", id="export-stats")

            # Insights Section
            with Vertical(id="insights", classes="analytics-section"):
                yield Static("💡 Insights & Recommendations", classes="section-title")
                yield DataTable(id="insights-table")
                with Horizontal(classes="analytics-controls"):
                    yield Button("🔍 Generate Insights", id="generate-insights")
                    yield Button("🔄 Refresh Insights", id="refresh-insights")

    def on_mount(self):
        """Initialize the analytics screen."""
        self._setup_command_table()
        self._setup_insights_table()
        self._load_command_stats()
        self._load_insights()

    def _get_analytics_status(self) -> str:
        """Get analytics status summary."""
        enabled = "🟢 Enabled" if is_analytics_enabled() else "🔴 Disabled"
        stats = get_command_stats()
        total_commands = sum(stats.values()) if stats else 0
        unique_commands = len(stats) if stats else 0
        return f"Status: {enabled} | Total Commands: {total_commands} | Unique Commands: {unique_commands}"

    def _get_analytics_settings(self) -> str:
        """Get analytics settings display."""
        enabled = is_analytics_enabled()
        
        lines = []
        lines.append(f"Analytics: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
        lines.append(f"Profile: {self.current_profile}")
        
        if enabled:
            stats = get_command_stats()
            total = sum(stats.values()) if stats else 0
            lines.append(f"Commands Tracked: {total}")
            lines.append(f"Unique Commands: {len(stats) if stats else 0}")
        else:
            lines.append("Enable analytics to track command usage and get insights")
        
        return "\n".join(lines)

    def _setup_command_table(self):
        """Setup the command usage table."""
        table = self.query_one("#command-table", DataTable)
        table.add_column("Rank", width=8)
        table.add_column("Command", width=30)
        table.add_column("Usage Count", width=15)
        table.add_column("Percentage", width=15)

    def _setup_insights_table(self):
        """Setup the insights table."""
        table = self.query_one("#insights-table", DataTable)
        table.add_column("Type", width=25)
        table.add_column("Severity", width=12)
        table.add_column("Message", width=60)

    def _load_command_stats(self):
        """Load command usage statistics into the table."""
        table = self.query_one("#command-table", DataTable)
        table.clear()

        if not is_analytics_enabled():
            table.add_row("N/A", "Analytics disabled", "0", "0%")
            return

        stats = get_command_stats()
        
        if not stats:
            table.add_row("N/A", "No data available", "0", "0%")
            return

        total = sum(stats.values())
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (command, count) in enumerate(sorted_stats, 1):
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(
                str(rank),
                command,
                str(count),
                f"{percentage:.1f}%"
            )

    def _load_insights(self):
        """Load insights into the table."""
        table = self.query_one("#insights-table", DataTable)
        table.clear()

        try:
            report = self.analyzer.generate_report()
            insights = report.get("insights", [])
            
            if not insights:
                table.add_row("info", "ℹ️", "No insights available - enable analytics and use EnvCLI to generate insights")
                return
            
            for insight in insights[:20]:  # Show first 20 insights
                insight_type = insight.get("type", "unknown").replace("_", " ").title()
                severity = insight.get("severity", "info")
                
                # Add emoji based on severity
                severity_emoji = {
                    "error": "❌",
                    "critical": "🔴",
                    "high": "🟠",
                    "warning": "⚠️",
                    "medium": "🟡",
                    "info": "ℹ️",
                    "suggestion": "💡"
                }.get(severity, "•")
                
                message = insight.get("message", "No message")
                
                table.add_row(
                    insight_type,
                    f"{severity_emoji} {severity}",
                    message[:60]
                )
        except Exception as e:
            table.add_row("error", "❌", f"Failed to load insights: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "enable-analytics":
            self._enable_analytics()
        elif button_id == "disable-analytics":
            self._disable_analytics()
        elif button_id == "refresh-analytics":
            self._refresh_analytics()
        elif button_id == "refresh-commands":
            self._refresh_commands()
        elif button_id == "export-stats":
            self._export_stats()
        elif button_id == "generate-insights":
            await self._generate_insights()
        elif button_id == "refresh-insights":
            self._refresh_insights()

    def _enable_analytics(self):
        """Enable analytics."""
        try:
            set_analytics_enabled(True)
            
            # Update displays
            status_widget = self.query_one("#analytics-status-text", Static)
            status_widget.update(self._get_analytics_status())
            
            settings_widget = self.query_one("#analytics-settings-display", Static)
            settings_widget.update(self._get_analytics_settings())
            
            self._load_command_stats()
            
            self.notify("Analytics enabled", severity="information")
        except Exception as e:
            self.notify(f"Failed to enable analytics: {e}", severity="error")

    def _disable_analytics(self):
        """Disable analytics."""
        try:
            set_analytics_enabled(False)
            
            # Update displays
            status_widget = self.query_one("#analytics-status-text", Static)
            status_widget.update(self._get_analytics_status())
            
            settings_widget = self.query_one("#analytics-settings-display", Static)
            settings_widget.update(self._get_analytics_settings())
            
            self._load_command_stats()
            
            self.notify("Analytics disabled", severity="warning")
        except Exception as e:
            self.notify(f"Failed to disable analytics: {e}", severity="error")

    def _refresh_analytics(self):
        """Refresh all analytics displays."""
        try:
            # Update status
            status_widget = self.query_one("#analytics-status-text", Static)
            status_widget.update(self._get_analytics_status())
            
            settings_widget = self.query_one("#analytics-settings-display", Static)
            settings_widget.update(self._get_analytics_settings())
            
            # Refresh tables
            self._load_command_stats()
            self._load_insights()
            
            self.notify("Analytics refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh analytics: {e}", severity="error")

    def _refresh_commands(self):
        """Refresh command statistics."""
        try:
            self._load_command_stats()
            self.notify("Command statistics refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh commands: {e}", severity="error")

    def _export_stats(self):
        """Export statistics to a file."""
        try:
            import json
            from pathlib import Path
            
            stats = get_command_stats()
            report = self.analyzer.generate_report()
            
            export_data = {
                "command_stats": stats,
                "insights_report": report,
                "exported_at": self.analyzer.data.get("last_analysis", "unknown")
            }
            
            export_file = Path.home() / ".envcli" / "analytics_export.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.notify(f"Statistics exported to: {export_file}", severity="information")
        except Exception as e:
            self.notify(f"Failed to export statistics: {e}", severity="error")

    async def _generate_insights(self):
        """Generate new insights."""
        try:
            self.notify("Generating insights...", severity="information")
            
            # Generate report
            report = self.analyzer.generate_report()
            
            # Refresh insights table
            self._load_insights()
            
            total = report.get("summary", {}).get("total_insights", 0)
            self.notify(f"Generated {total} insights", severity="information")
        except Exception as e:
            self.notify(f"Failed to generate insights: {e}", severity="error")

    def _refresh_insights(self):
        """Refresh insights display."""
        try:
            self._load_insights()
            self.notify("Insights refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh insights: {e}", severity="error")

