"""
Audit Logs screen for EnvCLI TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, DataTable, Input, Select, Label
from textual.message import Message
from datetime import datetime, timedelta

from ...rbac import RBACManager
from ...config import get_current_profile


class AuditScreen(Container):
    """Audit logs management screen."""

    def __init__(self):
        super().__init__()
        self.rbac_manager = RBACManager()
        self.current_profile = get_current_profile()
        self.filter_action = None
        self.filter_user = None
        self.current_limit = 100

    def compose(self) -> ComposeResult:
        """Compose the audit screen."""
        yield Static("📜 Audit Logs", id="audit-header", classes="screen-header")

        with VerticalScroll(id="audit-content"):
            # Audit status
            yield Static("📊 Audit Status", classes="section-title")
            yield Container(
                Static(self._get_audit_status(), id="audit-status-text"),
                classes="audit-status"
            )

            # Filters
            yield Static("🔍 Filters", classes="section-title")
            with Container(classes="audit-filters"):
                with Horizontal(classes="filter-row"):
                    yield Label("Action Type:")
                    yield Select(
                        [
                            ("All Actions", "all"),
                            ("User Added", "user_added"),
                            ("User Removed", "user_removed"),
                            ("Role Changed", "role_changed"),
                            ("Access Denied", "access_denied"),
                            ("Permissions Changed", "role_permissions_changed"),
                        ],
                        id="action-filter-select",
                        prompt="Filter by action",
                        classes="audit-select"
                    )
                    yield Label("User:")
                    yield Input(
                        placeholder="Filter by user",
                        id="user-filter-input",
                        classes="audit-input"
                    )
                    yield Label("Limit:")
                    yield Select(
                        [
                            ("Last 50", "50"),
                            ("Last 100", "100"),
                            ("Last 500", "500"),
                            ("Last 1000", "1000"),
                        ],
                        id="limit-select",
                        value="100",
                        classes="audit-select"
                    )

            with Horizontal(classes="button-row"):
                yield Button("🔍 Apply Filters", id="apply-filters-btn", variant="primary")
                yield Button("🔄 Clear Filters", id="clear-filters-btn", variant="default")
                yield Button("🔄 Refresh", id="refresh-audit-btn", variant="default")

            # Audit log table
            yield Static("📋 Audit Log Entries", classes="section-title")
            yield DataTable(id="audit-table", classes="audit-table")

            # Entry details
            yield Static("📝 Entry Details", classes="section-title")
            yield Container(
                Static("Select an entry to view details", id="entry-details"),
                classes="entry-details"
            )

            # Export options
            with Horizontal(classes="button-row"):
                yield Button("📄 Export to JSON", id="export-json-btn", variant="primary")
                yield Button("📊 Export to CSV", id="export-csv-btn", variant="primary")
                yield Button("🗑️ Clear Old Logs", id="clear-old-logs-btn", variant="error")

    def on_mount(self) -> None:
        """Initialize tables when screen is mounted."""
        self._setup_audit_table()
        self._load_audit_logs()

    def _get_audit_status(self) -> str:
        """Get audit status summary."""
        logs = self.rbac_manager.get_audit_log(limit=1000)
        total_entries = len(logs)

        # Count by action type
        action_counts = {}
        for entry in logs:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        # Get recent activity
        recent_count = len([e for e in logs if self._is_recent(e.get("timestamp", ""), hours=24)])

        status = f"📊 Total Entries: {total_entries}\n"
        status += f"🕐 Last 24 hours: {recent_count}\n"
        status += f"📁 Current Profile: {self.current_profile}\n"

        if action_counts:
            top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            status += "\n🔝 Top Actions:\n"
            for action, count in top_actions:
                status += f"  • {action}: {count}\n"

        return status

    def _is_recent(self, timestamp_str: str, hours: int = 24) -> bool:
        """Check if a timestamp is within the last N hours."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            cutoff = datetime.now() - timedelta(hours=hours)
            return timestamp >= cutoff
        except:
            return False

    def _setup_audit_table(self) -> None:
        """Setup the audit log table."""
        table = self.query_one("#audit-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Timestamp", "Action", "Performed By", "Details")
        table.cursor_type = "row"

    def _load_audit_logs(self) -> None:
        """Load audit logs into the table."""
        table = self.query_one("#audit-table", DataTable)
        table.clear()

        logs = self.rbac_manager.get_audit_log(limit=self.current_limit)

        # Apply filters
        filtered_logs = self._apply_filters(logs)

        # Sort by timestamp (most recent first)
        filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        for entry in filtered_logs:
            timestamp = entry.get("timestamp", "N/A")[:19]  # Truncate ISO format
            action = entry.get("action", "unknown")
            performed_by = entry.get("performed_by", "unknown")
            details = self._format_details(entry.get("details", {}))

            table.add_row(timestamp, action, performed_by, details)

    def _apply_filters(self, logs: list) -> list:
        """Apply filters to audit logs."""
        filtered = logs

        # Filter by action
        if self.filter_action and self.filter_action != "all":
            filtered = [e for e in filtered if e.get("action") == self.filter_action]

        # Filter by user
        if self.filter_user:
            filtered = [e for e in filtered
                       if self.filter_user.lower() in e.get("performed_by", "").lower()]

        return filtered

    def _format_details(self, details: dict) -> str:
        """Format details dictionary for display."""
        if not details:
            return "N/A"

        parts = []
        for key, value in details.items():
            if isinstance(value, (list, dict)):
                parts.append(f"{key}=...")
            else:
                parts.append(f"{key}={value}")

        return ", ".join(parts)[:50]  # Truncate long details

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "action-filter-select":
            self.filter_action = event.value
        elif event.select.id == "limit-select":
            self.current_limit = int(event.value)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "user-filter-input":
            self.filter_user = event.value

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in audit table."""
        if event.data_table.id == "audit-table":
            row_key = event.row_key
            table = event.data_table
            row_data = table.get_row(row_key)

            # Get full entry details
            logs = self.rbac_manager.get_audit_log(limit=self.current_limit)
            filtered_logs = self._apply_filters(logs)
            filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            if event.cursor_row < len(filtered_logs):
                entry = filtered_logs[event.cursor_row]
                self._show_entry_details(entry)

    def _show_entry_details(self, entry: dict) -> None:
        """Show detailed information about an audit entry."""
        details_widget = self.query_one("#entry-details", Static)

        timestamp = entry.get("timestamp", "N/A")
        action = entry.get("action", "unknown")
        performed_by = entry.get("performed_by", "unknown")
        details = entry.get("details", {})

        details_text = f"🕐 Timestamp: {timestamp}\n"
        details_text += f"⚡ Action: {action}\n"
        details_text += f"👤 Performed By: {performed_by}\n"

        if details:
            details_text += "\n📋 Details:\n"
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    import json
                    value_str = json.dumps(value, indent=2)
                    details_text += f"  • {key}:\n{value_str}\n"
                else:
                    details_text += f"  • {key}: {value}\n"

        details_widget.update(details_text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "apply-filters-btn":
            await self._apply_filters_action()
        elif button_id == "clear-filters-btn":
            await self._clear_filters()
        elif button_id == "refresh-audit-btn":
            await self._refresh_audit()
        elif button_id == "export-json-btn":
            await self._export_json()
        elif button_id == "export-csv-btn":
            await self._export_csv()
        elif button_id == "clear-old-logs-btn":
            await self._clear_old_logs()

    async def _apply_filters_action(self) -> None:
        """Apply filters and reload the table."""
        self._load_audit_logs()
        self._update_status()
        self.notify("🔍 Filters applied", severity="information")

    async def _clear_filters(self) -> None:
        """Clear all filters."""
        self.filter_action = None
        self.filter_user = None
        self.query_one("#user-filter-input", Input).value = ""
        self._load_audit_logs()
        self._update_status()
        self.notify("🔄 Filters cleared", severity="information")

    async def _refresh_audit(self) -> None:
        """Refresh the audit log display."""
        self._load_audit_logs()
        self._update_status()
        self.notify("🔄 Audit logs refreshed", severity="information")

    async def _export_json(self) -> None:
        """Export audit logs to JSON."""
        try:
            logs = self.rbac_manager.get_audit_log(limit=self.current_limit)
            filtered_logs = self._apply_filters(logs)

            import json
            from pathlib import Path

            export_file = Path.home() / "envcli_audit_export.json"
            with open(export_file, 'w') as f:
                json.dump(filtered_logs, f, indent=2)

            self.notify(f"✅ Exported {len(filtered_logs)} entries to {export_file}", severity="information")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    async def _export_csv(self) -> None:
        """Export audit logs to CSV."""
        try:
            logs = self.rbac_manager.get_audit_log(limit=self.current_limit)
            filtered_logs = self._apply_filters(logs)

            from pathlib import Path
            import csv

            export_file = Path.home() / "envcli_audit_export.csv"
            with open(export_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Action", "Performed By", "Details"])

                for entry in filtered_logs:
                    writer.writerow([
                        entry.get("timestamp", ""),
                        entry.get("action", ""),
                        entry.get("performed_by", ""),
                        self._format_details(entry.get("details", {}))
                    ])

            self.notify(f"✅ Exported {len(filtered_logs)} entries to {export_file}", severity="information")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    async def _clear_old_logs(self) -> None:
        """Clear old audit log entries."""
        self.notify("⚠️ Clear old logs feature requires confirmation - not implemented in TUI", severity="warning")

    def _update_status(self) -> None:
        """Update the audit status display."""
        status_widget = self.query_one("#audit-status-text", Static)
        status_widget.update(self._get_audit_status())

