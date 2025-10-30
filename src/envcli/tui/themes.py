"""
Theme system for EnvCLI TUI with multiple selectable themes
"""

from dataclasses import dataclass
from typing import Dict
from pathlib import Path
import json


@dataclass
class ThemeColors:
    """Color scheme for a theme."""
    # Main colors
    background: str
    surface: str
    primary: str
    secondary: str
    accent: str
    
    # Status colors
    warning: str
    error: str
    success: str
    info: str
    
    # Text colors
    text: str
    text_dim: str
    
    # Border colors
    border: str
    border_focus: str
    
    # Sidebar specific
    sidebar_bg: str
    sidebar_title_bg: str
    sidebar_title_text: str
    sidebar_hover: str
    sidebar_active: str


# Built-in themes
THEMES: Dict[str, ThemeColors] = {
    "github_dark": ThemeColors(
        background="#0D1117",
        surface="#161B22",
        primary="#58A6FF",
        secondary="#1F6FEB",
        accent="#79C0FF",
        warning="#D29922",
        error="#F85149",
        success="#3FB950",
        info="#58A6FF",
        text="#C9D1D9",
        text_dim="#8B949E",
        border="#30363D",
        border_focus="#58A6FF",
        sidebar_bg="#0D1117",
        sidebar_title_bg="#58A6FF",
        sidebar_title_text="#0D1117",
        sidebar_hover="#161B22",
        sidebar_active="#1A2332",
    ),
    "dracula": ThemeColors(
        background="#282A36",
        surface="#44475A",
        primary="#BD93F9",
        secondary="#8BE9FD",
        accent="#FF79C6",
        warning="#FFB86C",
        error="#FF5555",
        success="#50FA7B",
        info="#8BE9FD",
        text="#F8F8F2",
        text_dim="#6272A4",
        border="#44475A",
        border_focus="#BD93F9",
        sidebar_bg="#282A36",
        sidebar_title_bg="#BD93F9",
        sidebar_title_text="#282A36",
        sidebar_hover="#44475A",
        sidebar_active="#6272A4",
    ),
    "nord": ThemeColors(
        background="#2E3440",
        surface="#3B4252",
        primary="#88C0D0",
        secondary="#81A1C1",
        accent="#8FBCBB",
        warning="#EBCB8B",
        error="#BF616A",
        success="#A3BE8C",
        info="#5E81AC",
        text="#ECEFF4",
        text_dim="#4C566A",
        border="#434C5E",
        border_focus="#88C0D0",
        sidebar_bg="#2E3440",
        sidebar_title_bg="#88C0D0",
        sidebar_title_text="#2E3440",
        sidebar_hover="#3B4252",
        sidebar_active="#434C5E",
    ),
    "monokai": ThemeColors(
        background="#272822",
        surface="#3E3D32",
        primary="#66D9EF",
        secondary="#A6E22E",
        accent="#F92672",
        warning="#E6DB74",
        error="#F92672",
        success="#A6E22E",
        info="#66D9EF",
        text="#F8F8F2",
        text_dim="#75715E",
        border="#49483E",
        border_focus="#66D9EF",
        sidebar_bg="#272822",
        sidebar_title_bg="#66D9EF",
        sidebar_title_text="#272822",
        sidebar_hover="#3E3D32",
        sidebar_active="#49483E",
    ),
    "solarized_dark": ThemeColors(
        background="#002B36",
        surface="#073642",
        primary="#268BD2",
        secondary="#2AA198",
        accent="#6C71C4",
        warning="#B58900",
        error="#DC322F",
        success="#859900",
        info="#268BD2",
        text="#839496",
        text_dim="#586E75",
        border="#073642",
        border_focus="#268BD2",
        sidebar_bg="#002B36",
        sidebar_title_bg="#268BD2",
        sidebar_title_text="#002B36",
        sidebar_hover="#073642",
        sidebar_active="#094656",
    ),
    "tokyo_night": ThemeColors(
        background="#1A1B26",
        surface="#24283B",
        primary="#7AA2F7",
        secondary="#BB9AF7",
        accent="#7DCFFF",
        warning="#E0AF68",
        error="#F7768E",
        success="#9ECE6A",
        info="#7AA2F7",
        text="#C0CAF5",
        text_dim="#565F89",
        border="#414868",
        border_focus="#7AA2F7",
        sidebar_bg="#1A1B26",
        sidebar_title_bg="#7AA2F7",
        sidebar_title_text="#1A1B26",
        sidebar_hover="#24283B",
        sidebar_active="#2F3549",
    ),
    "gruvbox": ThemeColors(
        background="#282828",
        surface="#3C3836",
        primary="#83A598",
        secondary="#8EC07C",
        accent="#D3869B",
        warning="#FABD2F",
        error="#FB4934",
        success="#B8BB26",
        info="#83A598",
        text="#EBDBB2",
        text_dim="#928374",
        border="#504945",
        border_focus="#83A598",
        sidebar_bg="#282828",
        sidebar_title_bg="#83A598",
        sidebar_title_text="#282828",
        sidebar_hover="#3C3836",
        sidebar_active="#504945",
    ),
    "catppuccin": ThemeColors(
        background="#1E1E2E",
        surface="#313244",
        primary="#89B4FA",
        secondary="#94E2D5",
        accent="#F5C2E7",
        warning="#F9E2AF",
        error="#F38BA8",
        success="#A6E3A1",
        info="#89B4FA",
        text="#CDD6F4",
        text_dim="#6C7086",
        border="#45475A",
        border_focus="#89B4FA",
        sidebar_bg="#1E1E2E",
        sidebar_title_bg="#89B4FA",
        sidebar_title_text="#1E1E2E",
        sidebar_hover="#313244",
        sidebar_active="#45475A",
    ),
}


class ThemeManager:
    """Manages theme selection and persistence."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "theme.json"
        self._current_theme = "github_dark"
        self.load()
    
    def load(self):
        """Load theme preference from config."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    theme_name = data.get("theme", "github_dark")
                    if theme_name in THEMES:
                        self._current_theme = theme_name
            except Exception:
                pass
    
    def save(self):
        """Save theme preference to config."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w') as f:
                json.dump({"theme": self._current_theme}, f)
        except Exception:
            pass
    
    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """Set current theme."""
        if theme_name in THEMES:
            self._current_theme = theme_name
            self.save()
            return True
        return False
    
    def get_colors(self) -> ThemeColors:
        """Get colors for current theme."""
        return THEMES[self._current_theme]
    
    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list(THEMES.keys())


def generate_css(colors: ThemeColors) -> str:
    """Generate CSS from theme colors."""
    return f"""
Screen {{
    background: {colors.background};
}}

Header {{
    dock: top;
    height: 3;
    background: {colors.surface};
    color: {colors.text};
    border-bottom: solid {colors.border};
}}

Sidebar {{
    dock: left;
    width: 30;
    background: {colors.sidebar_bg};
    border-right: solid {colors.border};
}}

ContentPanel {{
    background: {colors.background};
    padding: 1 2;
}}

Footer {{
    dock: bottom;
    height: 3;
    background: {colors.surface};
    color: {colors.text};
    border-top: solid {colors.border};
}}

Button {{
    background: {colors.primary};
    color: {colors.background};
    border: none;
    min-width: 16;
}}

Button:hover {{
    background: {colors.secondary};
}}

Button.-warning {{
    background: {colors.warning};
}}

Button.-error {{
    background: {colors.error};
}}

Input {{
    background: {colors.surface};
    border: solid {colors.border};
    color: {colors.text};
}}

Input:focus {{
    border: solid {colors.border_focus};
}}

DataTable {{
    background: {colors.surface};
    color: {colors.text};
}}

DataTable > .datatable--header {{
    background: {colors.sidebar_hover};
    color: {colors.primary};
}}

DataTable > .datatable--cursor {{
    background: {colors.primary};
    color: {colors.background};
}}

.panel {{
    background: {colors.surface};
    border: solid {colors.border};
    padding: 1;
    margin: 1;
}}

.panel-title {{
    color: {colors.primary};
    text-style: bold;
}}

.stat-card {{
    background: {colors.surface};
    border: solid {colors.border};
    padding: 1;
    height: 7;
}}

.stat-value {{
    color: {colors.primary};
    text-style: bold;
    text-align: center;
}}

.stat-label {{
    color: {colors.text_dim};
    text-align: center;
}}

.alert {{
    background: {colors.surface};
    border-left: thick {colors.warning};
    padding: 1;
    margin: 1 0;
}}

.alert-error {{
    border-left: thick {colors.error};
}}

.alert-success {{
    border-left: thick {colors.success};
}}

.alert-info {{
    border-left: thick {colors.info};
}}

.masked {{
    color: {colors.text_dim};
}}

.key {{
    color: {colors.accent};
    text-style: bold;
}}

.value {{
    color: {colors.text};
}}

.screen-title {{
    width: 100%;
    height: 3;
    content-align: center middle;
    background: {colors.surface};
    color: {colors.primary};
    text-style: bold;
}}

.action-bar {{
    width: 100%;
    height: 3;
    padding: 0 2;
    background: {colors.background};
}}

.action-bar Button {{
    margin: 0 1;
}}

.content-area {{
    width: 100%;
    height: 1fr;
    padding: 1 2;
}}

.placeholder-text {{
    width: 100%;
    height: auto;
    padding: 4;
    text-align: center;
    color: {colors.text_dim};
}}

.section-title {{
    width: 100%;
    height: 2;
    color: {colors.primary};
    text-style: bold;
    margin-top: 1;
    margin-bottom: 1;
}}

.stats-bar {{
    width: 100%;
    height: 3;
    background: {colors.surface};
    border: solid {colors.border};
    padding: 1;
    margin-bottom: 1;
}}

.stats-bar Text {{
    color: {colors.text};
}}
"""

