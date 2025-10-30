"""
Theme selector screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Button, Static, Label
from textual.screen import ModalScreen
from textual.message import Message
from ..themes import ThemeManager, THEMES
from ...config import CONFIG_DIR


class ThemePreview(Container):
    """Preview card for a theme."""

    class ThemeSelected(Message):
        """Message sent when a theme is selected."""

        def __init__(self, theme_name: str):
            super().__init__()
            self.theme_name = theme_name

    def __init__(self, theme_name: str, is_active: bool = False):
        super().__init__()
        self.theme_name = theme_name
        self.is_active = is_active
        self.add_class("theme-preview")
        if is_active:
            self.add_class("-active")

    def compose(self) -> ComposeResult:
        """Compose theme preview."""
        colors = THEMES[self.theme_name]

        # Display name (convert snake_case to Title Case)
        display_name = self.theme_name.replace("_", " ").title()

        with Container(classes="preview-header"):
            yield Static(display_name, classes="preview-title")
            if self.is_active:
                yield Static("✓ ACTIVE", classes="preview-badge")

        # Color swatches - use Rich markup for colors
        from rich.text import Text
        swatches = Text()
        swatches.append("█ ", style=colors.primary)
        swatches.append("█ ", style=colors.secondary)
        swatches.append("█ ", style=colors.accent)
        swatches.append("█ ", style=colors.success)
        swatches.append("█ ", style=colors.warning)
        swatches.append("█", style=colors.error)

        yield Static(swatches, classes="preview-swatches")
        yield Button("Select", classes="preview-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle select button press."""
        self.post_message(self.ThemeSelected(self.theme_name))


class ThemeSelector(ModalScreen):
    """Modal screen for selecting themes."""
    
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
        ("ctrl+q", "dismiss", "Close"),
    ]
    
    DEFAULT_CSS = """
    ThemeSelector {
    align: center middle;
    }

    #theme-container {
        width: 95;
        height: 85;
        background: $surface;
        border: thick $primary;
        padding: 3;
    }

    .selector-title {
        width: 100%;
        height: 4;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        background: $surface-lighten-2;
        border: solid $border;
        margin-bottom: 2;
        text-align: center;
    }

    .selector-subtitle {
        width: 100%;
        height: 2;
    text-align: center;
    color: $text-muted;
    margin-bottom: 3;
    text-style: italic;
    }

    #themes-scroll {
        width: 100%;
        height: 1fr;
        margin-bottom: 3;
        overflow-y: auto;
    }

    .themes-grid {
    width: 100%;
    height: auto;
    layout: grid;
    grid-size: 3;
    grid-gutter: 2 3;
        padding: 1;
    }

    .theme-preview {
        width: 100%;
        height: 13;
        background: $surface-darken-1;
        border: solid $border;
        padding: 1;
    }

    .theme-preview:hover {
        border: solid $primary;
        background: $surface-lighten-1;
    }

    .theme-preview.-active {
        border: thick $success;
        background: $success 10%;
    }

    .preview-header {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .preview-title {
        width: 100%;
        height: auto;
        text-style: bold;
        color: $text;
        text-align: center;
    }

    .preview-badge {
        width: 100%;
        height: auto;
        color: $success;
        text-style: bold;
        text-align: center;
        background: $success 20%;
    }

    .preview-swatches {
        width: 100%;
        height: 2;
        text-align: center;
        margin: 1 0;
        background: $surface-darken-2;
    }

    .preview-button {
        width: 100%;
        height: 3;
        background: $primary;
        color: $background;
        border: none;
        text-style: bold;
    }

    .preview-button:hover {
        background: $primary-lighten-1;
    }

    .selector-actions {
        width: 100%;
        height: 4;
        align: center middle;
        background: $surface-darken-1;
        border: solid $border;
        padding: 1;
    }

    .selector-actions Button {
        margin: 0 2;
        min-width: 18;
        height: 2;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager(CONFIG_DIR)
        self.current_theme = self.theme_manager.get_current_theme()
    
    def compose(self) -> ComposeResult:
        """Compose theme selector."""
        with Container(id="theme-container"):
            yield Static("Select Theme", classes="selector-title")
            yield Static(
                f"Current: {self.current_theme.replace('_', ' ').title()}",
                classes="selector-subtitle"
            )
            
            with VerticalScroll(id="themes-scroll"):
                with Container(classes="themes-grid"):
                    for theme_name in self.theme_manager.get_available_themes():
                        is_active = theme_name == self.current_theme
                        yield ThemePreview(theme_name, is_active)
            
            with Horizontal(classes="selector-actions"):
                yield Button("Close", variant="error", id="close")
                yield Button("Cancel", variant="default", id="cancel")
    
    def action_dismiss(self) -> None:
        """Handle dismiss action from keyboard bindings."""
        self.dismiss(None)
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Handle both close and cancel buttons
        if event.button.id in ["close", "cancel"]:
            self.dismiss(None)
            event.stop()  # Stop propagation after handling

    def on_theme_preview_theme_selected(self, message: ThemePreview.ThemeSelected) -> None:
        """Handle theme selection."""
        theme_name = message.theme_name
        if self.theme_manager.set_theme(theme_name):
            # Apply theme immediately
            self.apply_theme()
            self.app.notify(
                f"Theme changed to {theme_name.replace('_', ' ').title()}",
                title="Theme Changed",
                severity="information"
            )
            self.dismiss(theme_name)

    def apply_theme(self) -> None:
        """Apply the current theme to the app."""
        # Reload theme across entire app
        self.app.reload_theme()

