"""
Footer component for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from rich.text import Text


class Footer(Container):
    """Footer bar with keyboard shortcuts and status."""
    
    DEFAULT_CSS = """
    Footer {
        dock: bottom;
        height: 3;
        background: #1A2332;
        color: #E0E0E0;
        border-top: solid #37474F;
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
        yield Static(self._render_shortcuts(), classes="footer-left")
        yield Static(self._render_status(), classes="footer-right")
    
    def _render_shortcuts(self) -> Text:
        """Render keyboard shortcuts."""
        text = Text()

        shortcuts = [
            ("Ctrl+K", "Search"),
            ("/", "Commands"),
            ("Q", "Quit"),
        ]

        for i, (key, action) in enumerate(shortcuts):
            if i > 0:
                text.append(" | ", style="#757575")
            text.append(key, style="bold #64FFDA")
            text.append(f" {action}", style="#E0E0E0")

        return text
    
    def _render_status(self) -> Text:
        """Render status information."""
        text = Text()
        text.append("Press ", style="#757575")
        text.append("?", style="bold #64FFDA")
        text.append(" for help", style="#757575")
        return text

