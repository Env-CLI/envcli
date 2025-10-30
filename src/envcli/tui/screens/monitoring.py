"""
Monitoring screen for EnvCLI TUI.
"""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Select, DataTable, Label, Input
from textual.message import Message
from ...monitoring import MonitoringSystem
from ...config import get_current_profile


class MonitoringScreen(Container):
    """Monitoring and alerting management screen."""

    DEFAULT_CSS = """
    MonitoringScreen {
        layout: vertical;
        height: 100%;
    }

    #monitoring-header {
        dock: top;
        height: auto;
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    #monitoring-content {
        height: 1fr;
    }

    .monitoring-section {
        border: solid $primary;
        height: auto;
        margin: 1;
        padding: 1;
    }

    .monitoring-controls {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }

    .monitoring-controls Button {
        margin-right: 1;
    }

    #health-status {
        height: 8;
    }

    #alert-channels {
        height: 12;
    }

    #recent-alerts {
        height: 1fr;
    }

    #alerts-table {
        height: 1fr;
    }
    """

    def __init__(self):
        super().__init__()
        self.monitor = MonitoringSystem()
        self.current_profile = get_current_profile()

    def compose(self):
        """Compose the monitoring screen."""
        with VerticalScroll(id="monitoring-content"):
            # Header
            with Vertical(id="monitoring-header"):
                yield Static("📊 Monitoring & Alerts", classes="header-title")
                yield Static(self._get_monitoring_status(), id="monitoring-status")

            # Health Status Section
            with Vertical(id="health-status", classes="monitoring-section"):
                yield Static("🏥 Health Status", classes="section-title")
                yield Static(self._get_health_status_display(), id="health-display")
                with Horizontal(classes="monitoring-controls"):
                    yield Button("🔄 Run Health Check", id="run-health-check")
                    yield Button("✅ Enable Monitoring", id="enable-monitoring")
                    yield Button("❌ Disable Monitoring", id="disable-monitoring")

            # Alert Channels Section
            with Vertical(id="alert-channels", classes="monitoring-section"):
                yield Static("📢 Alert Channels", classes="section-title")
                with Horizontal(classes="monitoring-controls"):
                    yield Label("Webhook URL:")
                    yield Input(placeholder="https://hooks.example.com/...", id="webhook-url")
                    yield Button("➕ Add Webhook", id="add-webhook")
                with Horizontal(classes="monitoring-controls"):
                    yield Label("Slack Webhook:")
                    yield Input(placeholder="https://hooks.slack.com/...", id="slack-url")
                    yield Button("➕ Add Slack", id="add-slack")

            # Recent Alerts Section
            with Vertical(id="recent-alerts", classes="monitoring-section"):
                yield Static("🚨 Recent Alerts", classes="section-title")
                yield DataTable(id="alerts-table")
                with Horizontal(classes="monitoring-controls"):
                    yield Button("🔄 Refresh Alerts", id="refresh-alerts")
                    yield Button("🗑️ Clear Alerts", id="clear-alerts")

    def on_mount(self):
        """Initialize the monitoring screen."""
        self._setup_alerts_table()
        self._load_alerts()

    def _get_monitoring_status(self) -> str:
        """Get monitoring status summary."""
        status = self.monitor.get_health_status()
        enabled = "🟢 Enabled" if status.get("status") == "active" else "🔴 Disabled"
        last_check = status.get("last_check", "Never")
        channels = status.get("alert_channels", 0)
        return f"Status: {enabled} | Last Check: {last_check[:19] if last_check != 'Never' else 'Never'} | Channels: {channels}"

    def _get_health_status_display(self) -> str:
        """Get detailed health status display."""
        status = self.monitor.get_health_status()
        
        lines = []
        lines.append(f"Status: {status.get('status', 'unknown').upper()}")
        lines.append(f"Last Check: {status.get('last_check', 'Never')[:19] if status.get('last_check') != 'Never' else 'Never'}")
        lines.append(f"Time Since Check: {status.get('time_since_check', 'N/A')}")
        lines.append(f"Alert Channels: {status.get('alert_channels', 0)}")
        lines.append(f"Total Alerts: {status.get('total_alerts', 0)}")
        
        return "\n".join(lines)

    def _setup_alerts_table(self):
        """Setup the alerts table."""
        table = self.query_one("#alerts-table", DataTable)
        table.add_column("ID", width=20)
        table.add_column("Type", width=20)
        table.add_column("Severity", width=12)
        table.add_column("Message", width=40)
        table.add_column("Timestamp", width=20)
        table.add_column("Status", width=12)

    def _load_alerts(self):
        """Load recent alerts into the table."""
        table = self.query_one("#alerts-table", DataTable)
        table.clear()

        alerts = self.monitor.list_alerts(limit=20)
        
        for alert in alerts:
            table.add_row(
                alert.get("id", "")[:20],
                alert.get("type", "unknown"),
                alert.get("severity", "info"),
                alert.get("message", "")[:40],
                alert.get("timestamp", "")[:19],
                "✅ Resolved" if alert.get("resolved", False) else "⚠️ Active"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "run-health-check":
            await self._run_health_check()
        elif button_id == "enable-monitoring":
            self._enable_monitoring()
        elif button_id == "disable-monitoring":
            self._disable_monitoring()
        elif button_id == "add-webhook":
            self._add_webhook()
        elif button_id == "add-slack":
            self._add_slack()
        elif button_id == "refresh-alerts":
            self._refresh_alerts()
        elif button_id == "clear-alerts":
            self._clear_alerts()

    async def _run_health_check(self):
        """Run a health check."""
        try:
            results = self.monitor.run_health_check()
            
            # Update displays
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            health_widget = self.query_one("#health-display", Static)
            health_widget.update(self._get_health_status_display())
            
            # Refresh alerts
            self._load_alerts()
            
            # Show results
            checks = results.get("checks", {})
            alerts_triggered = len(results.get("alerts_triggered", []))
            
            result_text = f"Health check completed!\n"
            for check_name, check_data in checks.items():
                status = check_data.get("status", "unknown")
                result_text += f"  {check_name}: {status}\n"
            
            if alerts_triggered > 0:
                result_text += f"\n⚠️ {alerts_triggered} alerts triggered"
            
            self.notify(result_text, severity="information")
            
        except Exception as e:
            self.notify(f"Health check failed: {e}", severity="error")

    def _enable_monitoring(self):
        """Enable monitoring."""
        try:
            self.monitor.enable_monitoring()
            
            # Update displays
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            health_widget = self.query_one("#health-display", Static)
            health_widget.update(self._get_health_status_display())
            
            self.notify("Monitoring enabled", severity="information")
        except Exception as e:
            self.notify(f"Failed to enable monitoring: {e}", severity="error")

    def _disable_monitoring(self):
        """Disable monitoring."""
        try:
            self.monitor.disable_monitoring()
            
            # Update displays
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            health_widget = self.query_one("#health-display", Static)
            health_widget.update(self._get_health_status_display())
            
            self.notify("Monitoring disabled", severity="warning")
        except Exception as e:
            self.notify(f"Failed to disable monitoring: {e}", severity="error")

    def _add_webhook(self):
        """Add a webhook alert channel."""
        try:
            url_input = self.query_one("#webhook-url", Input)
            url = url_input.value.strip()
            
            if not url:
                self.notify("Please enter a webhook URL", severity="warning")
                return
            
            self.monitor.add_alert_channel("webhook", {"url": url})
            
            # Update status
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            # Clear input
            url_input.value = ""
            
            self.notify(f"Webhook added: {url}", severity="information")
        except Exception as e:
            self.notify(f"Failed to add webhook: {e}", severity="error")

    def _add_slack(self):
        """Add a Slack alert channel."""
        try:
            url_input = self.query_one("#slack-url", Input)
            url = url_input.value.strip()
            
            if not url:
                self.notify("Please enter a Slack webhook URL", severity="warning")
                return
            
            self.monitor.add_alert_channel("slack", {"webhook_url": url})
            
            # Update status
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            # Clear input
            url_input.value = ""
            
            self.notify(f"Slack webhook added: {url}", severity="information")
        except Exception as e:
            self.notify(f"Failed to add Slack webhook: {e}", severity="error")

    def _refresh_alerts(self):
        """Refresh the alerts list."""
        try:
            self._load_alerts()
            self.notify("Alerts refreshed", severity="information")
        except Exception as e:
            self.notify(f"Failed to refresh alerts: {e}", severity="error")

    def _clear_alerts(self):
        """Clear all alerts."""
        try:
            # Clear alerts in the monitoring system
            self.monitor.alerts = []
            self.monitor._save_alerts()
            
            # Refresh display
            self._load_alerts()
            
            # Update status
            status_widget = self.query_one("#monitoring-status", Static)
            status_widget.update(self._get_monitoring_status())
            
            health_widget = self.query_one("#health-display", Static)
            health_widget.update(self._get_health_status_display())
            
            self.notify("All alerts cleared", severity="information")
        except Exception as e:
            self.notify(f"Failed to clear alerts: {e}", severity="error")

