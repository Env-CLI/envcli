"""Events & Hooks screen for EnvCLI TUI."""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Select, DataTable, Label, Input
from textual.message import Message
from ...event_hooks import event_manager, trigger_env_changed, trigger_profile_created, trigger_sync_completed
from ...config import get_current_profile


class EventsScreen(Container):
    """Events and hooks management screen."""
    
    DEFAULT_CSS = """
    EventsScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }
    
    .status-box {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }
    
    .section {
        border: solid $accent;
        padding: 1;
        margin-top: 1;
        height: auto;
    }
    
    .button-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    
    .button-row Button {
        margin-right: 1;
    }
    
    .input-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    
    .input-row Label {
        width: 15;
        padding-right: 1;
    }
    
    .input-row Input {
        width: 1fr;
    }
    
    DataTable {
        height: 20;
        margin-top: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.selected_event = None
    
    def compose(self):
        """Compose the events screen."""
        with VerticalScroll():
            yield Static("🪝 Events & Hooks", classes="header")
            
            # Events status
            yield Static(self._get_events_status(), id="events-status", classes="status-box")
            
            # Add webhook section
            with Vertical(classes="section"):
                yield Static("➕ Add Webhook", classes="header")
                with Horizontal(classes="input-row"):
                    yield Label("Event Type:")
                    yield Select(
                        [
                            ("Environment Changed", "env_changed"),
                            ("Profile Created", "profile_created"),
                            ("Profile Deleted", "profile_deleted"),
                            ("Sync Completed", "sync_completed"),
                            ("Validation Failed", "validation_failed")
                        ],
                        id="event-type-selector"
                    )
                with Horizontal(classes="input-row"):
                    yield Label("Webhook URL:")
                    yield Input(placeholder="https://example.com/webhook", id="webhook-url-input")
                with Horizontal(classes="input-row"):
                    yield Label("Method:")
                    yield Select(
                        [("POST", "POST"), ("GET", "GET"), ("PUT", "PUT")],
                        value="POST",
                        id="webhook-method-selector"
                    )
                with Horizontal(classes="button-row"):
                    yield Button("➕ Add Webhook", id="add-webhook-btn", variant="success")
            
            # Add script hook section
            with Vertical(classes="section"):
                yield Static("📜 Add Script Hook", classes="header")
                with Horizontal(classes="input-row"):
                    yield Label("Event Type:")
                    yield Select(
                        [
                            ("Environment Changed", "env_changed"),
                            ("Profile Created", "profile_created"),
                            ("Profile Deleted", "profile_deleted"),
                            ("Sync Completed", "sync_completed"),
                            ("Validation Failed", "validation_failed")
                        ],
                        id="script-event-selector"
                    )
                with Horizontal(classes="input-row"):
                    yield Label("Script Path:")
                    yield Input(placeholder="/path/to/script.sh", id="script-path-input")
                with Horizontal(classes="button-row"):
                    yield Button("➕ Add Script", id="add-script-btn", variant="success")
            
            # Add command hook section
            with Vertical(classes="section"):
                yield Static("⚡ Add Command Hook", classes="header")
                with Horizontal(classes="input-row"):
                    yield Label("Event Type:")
                    yield Select(
                        [
                            ("Environment Changed", "env_changed"),
                            ("Profile Created", "profile_created"),
                            ("Profile Deleted", "profile_deleted"),
                            ("Sync Completed", "sync_completed"),
                            ("Validation Failed", "validation_failed")
                        ],
                        id="command-event-selector"
                    )
                with Horizontal(classes="input-row"):
                    yield Label("Command:")
                    yield Input(placeholder="echo 'Event triggered'", id="command-input")
                with Horizontal(classes="button-row"):
                    yield Button("➕ Add Command", id="add-command-btn", variant="success")
            
            # Hooks table
            yield Static("📋 Configured Hooks", classes="header")
            with Horizontal(classes="button-row"):
                yield Button("🔄 Refresh", id="refresh-btn")
                yield Button("🗑️ Remove Selected", id="remove-hook-btn", variant="error")
                yield Button("🧪 Test Event", id="test-event-btn")
            yield DataTable(id="hooks-table")
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        self._setup_hooks_table()
        self._load_hooks()
    
    def _get_events_status(self) -> str:
        """Get events status summary."""
        hooks = event_manager.list_hooks()
        
        total_hooks = sum(len(event_hooks) for event_hooks in hooks.values())
        enabled_hooks = sum(
            sum(1 for hook in event_hooks if hook.get("enabled", True))
            for event_hooks in hooks.values()
        )
        
        status = f"Total Hooks: {total_hooks}\n"
        status += f"Enabled: {enabled_hooks}\n"
        status += f"Disabled: {total_hooks - enabled_hooks}\n"
        status += f"Current Profile: {self.current_profile}"
        
        return status
    
    def _setup_hooks_table(self) -> None:
        """Setup the hooks table."""
        table = self.query_one("#hooks-table", DataTable)
        table.add_column("Event", key="event")
        table.add_column("Type", key="type")
        table.add_column("Config", key="config")
        table.add_column("Status", key="status")
        table.cursor_type = "row"
    
    async def _load_hooks(self) -> None:
        """Load configured hooks."""
        table = self.query_one("#hooks-table", DataTable)
        table.clear()
        
        hooks = event_manager.list_hooks()
        
        for event, event_hooks in hooks.items():
            for hook in event_hooks:
                status = "✅ Enabled" if hook.get("enabled", True) else "❌ Disabled"
                config_str = self._format_hook_config(hook)
                
                table.add_row(
                    event,
                    hook["type"],
                    config_str,
                    status
                )
    
    def _format_hook_config(self, hook: dict) -> str:
        """Format hook configuration for display."""
        config = hook.get("config", {})
        
        if hook["type"] == "webhook":
            return f"{config.get('method', 'POST')} {config.get('url', 'N/A')}"
        elif hook["type"] == "script":
            return config.get("path", "N/A")
        elif hook["type"] == "command":
            return config.get("command", "N/A")
        
        return str(config)
    
    async def _add_webhook(self) -> None:
        """Add a webhook hook."""
        event_selector = self.query_one("#event-type-selector", Select)
        url_input = self.query_one("#webhook-url-input", Input)
        method_selector = self.query_one("#webhook-method-selector", Select)
        
        event = event_selector.value
        url = url_input.value
        method = method_selector.value
        
        if not url:
            self.notify("⚠️ Please enter a webhook URL", severity="warning")
            return
        
        try:
            config = {
                "url": url,
                "method": method,
                "headers": {"Content-Type": "application/json"},
                "timeout": 10
            }
            
            event_manager.add_hook(event, "webhook", config)
            self.notify(f"✅ Webhook added for {event}", severity="information")
            
            # Clear input
            url_input.value = ""
            
            await self._load_hooks()
            await self._update_status()
        except Exception as e:
            self.notify(f"❌ Failed to add webhook: {e}", severity="error")
    
    async def _add_script(self) -> None:
        """Add a script hook."""
        event_selector = self.query_one("#script-event-selector", Select)
        path_input = self.query_one("#script-path-input", Input)
        
        event = event_selector.value
        path = path_input.value
        
        if not path:
            self.notify("⚠️ Please enter a script path", severity="warning")
            return
        
        try:
            config = {
                "path": path,
                "timeout": 30
            }
            
            event_manager.add_hook(event, "script", config)
            self.notify(f"✅ Script hook added for {event}", severity="information")
            
            # Clear input
            path_input.value = ""
            
            await self._load_hooks()
            await self._update_status()
        except Exception as e:
            self.notify(f"❌ Failed to add script: {e}", severity="error")
    
    async def _add_command(self) -> None:
        """Add a command hook."""
        event_selector = self.query_one("#command-event-selector", Select)
        command_input = self.query_one("#command-input", Input)
        
        event = event_selector.value
        command = command_input.value
        
        if not command:
            self.notify("⚠️ Please enter a command", severity="warning")
            return
        
        try:
            config = {
                "command": command,
                "timeout": 30
            }
            
            event_manager.add_hook(event, "command", config)
            self.notify(f"✅ Command hook added for {event}", severity="information")
            
            # Clear input
            command_input.value = ""
            
            await self._load_hooks()
            await self._update_status()
        except Exception as e:
            self.notify(f"❌ Failed to add command: {e}", severity="error")
    
    async def _remove_hook(self) -> None:
        """Remove selected hook."""
        table = self.query_one("#hooks-table", DataTable)
        
        if table.cursor_row is None or table.cursor_row < 0:
            self.notify("⚠️ Please select a hook to remove", severity="warning")
            return
        
        try:
            # Get the event and index from the selected row
            row_key = table.get_row_at(table.cursor_row)
            event = str(row_key[0])
            
            # Find the hook index for this event
            hooks = event_manager.list_hooks()
            event_hooks = hooks.get(event, [])
            
            if event_hooks:
                # Remove the first hook for this event (simplified)
                event_manager.remove_hook(event, 0)
                self.notify(f"✅ Hook removed from {event}", severity="information")
                
                await self._load_hooks()
                await self._update_status()
            else:
                self.notify("⚠️ No hooks found for this event", severity="warning")
        except Exception as e:
            self.notify(f"❌ Failed to remove hook: {e}", severity="error")
    
    async def _test_event(self) -> None:
        """Test triggering an event."""
        event_selector = self.query_one("#event-type-selector", Select)
        event = event_selector.value
        
        try:
            # Trigger a test event
            test_data = {
                "event": event,
                "profile": self.current_profile,
                "test": True
            }
            
            if event == "env_changed":
                results = trigger_env_changed(self.current_profile, {"test": "data"})
            elif event == "profile_created":
                results = trigger_profile_created(self.current_profile)
            elif event == "sync_completed":
                results = trigger_sync_completed("test", self.current_profile, True)
            else:
                results = event_manager.trigger_event(event, test_data)
            
            if results:
                self.notify(f"✅ Event triggered: {len(results)} hooks executed", severity="information")
            else:
                self.notify(f"⚠️ No hooks configured for {event}", severity="warning")
        except Exception as e:
            self.notify(f"❌ Failed to trigger event: {e}", severity="error")
    
    async def _update_status(self) -> None:
        """Update events status display."""
        status_widget = self.query_one("#events-status", Static)
        status_widget.update(self._get_events_status())
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "add-webhook-btn":
            await self._add_webhook()
        elif button_id == "add-script-btn":
            await self._add_script()
        elif button_id == "add-command-btn":
            await self._add_command()
        elif button_id == "refresh-btn":
            await self._load_hooks()
            await self._update_status()
        elif button_id == "remove-hook-btn":
            await self._remove_hook()
        elif button_id == "test-event-btn":
            await self._test_event()

