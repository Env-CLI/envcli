"""
Header component for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from rich.text import Text


class Header(Container):
    """Header bar with status indicators and current profile."""
    
    DEFAULT_CSS = """
    Header {
    dock: top;
    height: 3;
    }
    
    .header-left {
        dock: left;
        width: 40%;
        padding: 1 2;
    }
    
    .header-center {
        width: 20%;
        padding: 1 2;
        text-align: center;
    }
    
    .header-right {
        dock: right;
        width: 40%;
        padding: 1 2;
        text-align: right;
    }
    """
    
    def __init__(self, profile: str = "default", ai_provider: str = "none"):
        super().__init__()
        self.profile = profile
        self.ai_provider = ai_provider
    
    def compose(self) -> ComposeResult:
        """Compose header widgets."""
        yield Static(self._render_left(), classes="header-left")
        yield Static(self._render_center(), classes="header-center")
        yield Static(self._render_right(), classes="header-right")
    
    def _render_left(self) -> Text:
        """Render left section (app title and version)."""
        text = Text()
        text.append("EnvCLI ", style="bold #00E676")
        text.append("v3.0.0", style="#757575")
        return text
    
    def _render_center(self) -> Text:
        """Render center section (current profile)."""
        text = Text()
        text.append("/ ", style="#64FFDA")
        text.append(self.profile, style="bold #00E676")
        return text
    
    def _render_right(self) -> Text:
        """Render right section (AI provider and status)."""
        text = Text()
        
        # AI provider
        if self.ai_provider != "none":
            text.append("* ", style="#64FFDA")
            text.append(self.ai_provider, style="#00BFA5")
            text.append(" | ", style="#757575")
        
        # Status
        text.append("+ ", style="#00E676")
        text.append("Ready", style="#E0E0E0")
        
        return text
    
    def update_profile(self, profile: str):
        """Update current profile display."""
        self.profile = profile
        # Update the center static widget
        try:
            center = self.query_one(".header-center", Static)
            center.update(self._render_center())
        except:
            self.refresh()

    def update_ai_provider(self, provider: str):
        """Update AI provider display."""
        self.ai_provider = provider
        # Update the right static widget
        try:
            right = self.query_one(".header-right", Static)
            right.update(self._render_right())
        except:
            self.refresh()

