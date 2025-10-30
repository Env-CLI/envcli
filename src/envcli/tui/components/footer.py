"""
Footer component for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button


class Footer(Container):
    """Footer bar with keyboard shortcuts and status."""

    DEFAULT_CSS = """
    Footer {
    dock: bottom;
    height: 3;
    }

    .footer-left {
        dock: left;
        width: 60%;
        padding: 1 2;
    }

    .footer-right {
        dock: right;
        width: 40%;
        padding: 1 2;
        text-align: right;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose footer widgets."""
        yield Button("🔍 Ctrl+K", id="quick-search-btn")
        yield Button("📋 /", id="command-palette-btn")
        yield Button("❌ Q", id="quit-btn")
        yield Button("❓ ?", id="help-btn")

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        self.app.notify(f"Footer button pressed: {event.button.id}", severity="information")
        if event.button.id == "quick-search-btn":
            self.app.action_quick_search()
        elif event.button.id == "command-palette-btn":
            self.app.action_command_palette()
        elif event.button.id == "help-btn":
            self.app.action_help()
        elif event.button.id == "quit-btn":
            self.app.action_quit()

