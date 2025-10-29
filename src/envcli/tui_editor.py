"""
TUI Editor for environment variables using Textual.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Input, Button, Header, Footer, Static
from textual import events
from typing import Dict
from .env_manager import EnvManager

class EnvEditor(App):
    """TUI editor for environment variables."""

    CSS = """
    Screen {
        background: $surface;
    }

    DataTable {
        height: 1fr;
        border: solid $primary;
    }

    .editor-container {
        height: 1fr;
        padding: 1;
    }

    .input-container {
        height: 3;
        border: solid $secondary;
        padding: 1;
    }

    Button {
        margin: 1;
    }
    """

    def __init__(self, profile: str):
        super().__init__()
        self.profile = profile
        self.manager = EnvManager(profile)
        self.env_vars = self.manager.load_env()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="editor-container"):
            yield DataTable(id="env-table")
            with Vertical(classes="input-container"):
                with Horizontal():
                    yield Static("Key:", classes="label")
                    yield Input(placeholder="Enter key", id="key-input")
                with Horizontal():
                    yield Static("Value:", classes="label")
                    yield Input(placeholder="Enter value", id="value-input")
                with Horizontal():
                    yield Button("Add/Update", id="add-btn", variant="primary")
                    yield Button("Delete", id="delete-btn", variant="error")
                    yield Button("Save & Exit", id="save-btn", variant="success")
                    yield Button("Cancel", id="cancel-btn")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#env-table", DataTable)
        table.add_columns("Key", "Value")
        self.refresh_table()

    def refresh_table(self):
        """Refresh the data table with current env vars."""
        table = self.query_one("#env-table", DataTable)
        table.clear()

        for key, value in sorted(self.env_vars.items()):
            # Mask secrets
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                display_value = '*' * len(value)
            else:
                display_value = value
            table.add_row(key, display_value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self.add_env_var()
        elif event.button.id == "delete-btn":
            self.delete_env_var()
        elif event.button.id == "save-btn":
            self.save_and_exit()
        elif event.button.id == "cancel-btn":
            self.exit()

    def add_env_var(self):
        """Add or update an environment variable."""
        key_input = self.query_one("#key-input", Input)
        value_input = self.query_one("#value-input", Input)

        key = key_input.value.strip()
        value = value_input.value.strip()

        if key:
            self.env_vars[key] = value
            self.refresh_table()
            key_input.clear()
            value_input.clear()

    def delete_env_var(self):
        """Delete selected environment variable."""
        table = self.query_one("#env-table", DataTable)
        if table.cursor_row >= 0:
            key = list(sorted(self.env_vars.keys()))[table.cursor_row]
            if key in self.env_vars:
                del self.env_vars[key]
                self.refresh_table()

    def save_and_exit(self):
        """Save changes and exit."""
        self.manager.save_env(self.env_vars)
        self.exit()

def edit_env_tui(profile: str):
    """Launch the TUI editor for environment variables."""
    app = EnvEditor(profile)
    app.run()
