"""
Sidebar navigation component for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static
from textual.message import Message
from ..theme import get_module_icon
from ..themes import ThemeManager, generate_css
from pathlib import Path


class ModuleButton(Button):
    """Custom button for module navigation."""

    def __init__(self, module_id: str, label: str, icon: str):
        super().__init__(f"{icon}  {label}")
        self.module_id = module_id


class ModuleSeparator(Static):
    """Visual separator between module groups."""

    def __init__(self, label: str = ""):
        super().__init__(label)
        self.add_class("module-separator")


class Sidebar(Container):
    """Sidebar with module navigation."""

    def __init__(self):
        super().__init__()
        self.active_module = "dashboard"
        self.module_groups = [
            ("CORE", [
                ("dashboard", "Dashboard"),
                ("variables", "Variables"),
                ("profiles", "Profiles"),
            ]),
            ("SECURITY", [
                ("encryption", "Encryption"),
                ("rbac", "RBAC & Policy"),
                ("compliance", "Compliance"),
                ("audit", "Audit Logs"),
            ]),
            ("AUTOMATION", [
                ("ai_analysis", "AI Analysis"),
                ("rules", "Rules & Policies"),
                ("cicd", "CI/CD"),
                ("events", "Events & Hooks"),
            ]),
            ("INFRASTRUCTURE", [
                ("cloud_sync", "Cloud Sync"),
                ("kubernetes", "Kubernetes"),
                ("monitoring", "Monitoring"),
            ]),
            ("INSIGHTS", [
                ("analytics", "Analytics"),
                ("predict", "Predictive"),
            ]),
            ("SYSTEM", [
                ("settings", "⚙️ Settings"),
                ("plugins", "Plugins"),
            ]),
        ]

        # Load theme
        from ...config import CONFIG_DIR
        self.theme_manager = ThemeManager(CONFIG_DIR)
        self.update_css()

    def update_css(self):
        """Update CSS based on current theme."""
        # Reload theme manager to get latest theme
        self.theme_manager.load()
        colors = self.theme_manager.get_colors()

        # Apply inline styles to the sidebar itself
        from textual.color import Color
        self.styles.background = Color.parse(colors.sidebar_bg)

        # Update title
        try:
            title = self.query_one(".sidebar-title", Static)
            title.styles.background = Color.parse(colors.sidebar_title_bg)
            title.styles.color = Color.parse(colors.sidebar_title_text)
        except:
            pass

        # Update all module buttons
        for button in self.query("ModuleButton"):
            if button.has_class("-active"):
                button.styles.background = Color.parse(colors.sidebar_active)
                button.styles.color = Color.parse(colors.primary)
            else:
                button.styles.background = Color.parse("transparent")
                button.styles.color = Color.parse(colors.text_dim)

        # Update separators
        for sep in self.query(".module-separator"):
            sep.styles.color = Color.parse(colors.border)

        # Refresh to apply changes
        self.refresh(layout=True)

        # Store CSS template for new widgets
        self.DEFAULT_CSS = f"""
    Sidebar {{
        dock: left;
        width: 45;
        height: 100%;
        background: {colors.sidebar_bg};
        border-right: solid {colors.border};
    }}

    .sidebar-title {{
        dock: top;
        height: 5;
        padding: 1 2;
        background: {colors.primary};
        color: {colors.background};
        text-style: bold;
        text-align: center;
        content-align: center middle;
    }}

    .sidebar-scroll {{
        height: 100%;
        width: 100%;
        padding: 1 2;
        overflow-y: auto;
    }}

    ModuleButton {{
        width: 100%;
        height: auto;
        min-height: 5;
        background: transparent;
        color: {colors.text};
        border: none;
        border-left: solid transparent;
        text-align: left;
        padding: 2 4;
        margin: 0 0 1 0;
        text-style: bold;
        font-size: 1.1;
    }}

    ModuleButton:hover {{
        background: {colors.sidebar_hover};
        color: {colors.text};
        border-left: solid {colors.primary};
    }}

    ModuleButton.-active {{
        background: {colors.sidebar_active};
        color: {colors.primary};
        border-left: solid {colors.primary};
        text-style: bold;
    }}

    ModuleButton.settings-button {{
        background: #263238;
        color: {colors.warning};
        border-left: solid {colors.warning};
        border: 1px solid {colors.warning};
        text-style: bold;
        margin-bottom: 2;
    }}

    ModuleButton.settings-button:hover {{
        background: {colors.warning};
        color: {colors.background};
        border-left: solid {colors.background};
    }}

    ModuleButton.settings-button.-active {{
        background: {colors.warning};
        color: {colors.background};
        border-left: solid {colors.background};
    }}

    .module-separator {{
        width: 100%;
        height: 2;
        padding: 1 4;
        margin: 1 0 1 0;
        color: {colors.primary};
        text-style: bold;
        text-align: left;
        font-size: 1.2;
    }}
    """

    class ModuleSelected(Message):
        """Message sent when a module is selected."""

        def __init__(self, module_id: str):
            super().__init__()
            self.module_id = module_id
    
    def compose(self) -> ComposeResult:
        """Compose sidebar widgets."""
        yield Static("⬢ ENVCLI", classes="sidebar-title")

        with VerticalScroll(classes="sidebar-scroll"):
            for group_name, modules in self.module_groups:
                # Add group separator
                yield ModuleSeparator(f"▸ {group_name}")

                # Add modules in this group
                for module_id, label in modules:
                    # Use different styling for settings to make it more visible
                    if module_id == "settings":
                        # Settings gets a special style to stand out
                        icon = "⚙️"
                        button = ModuleButton(module_id, label, icon)
                        button.add_class("settings-button")
                    else:
                        icon = get_module_icon(module_id)
                        button = ModuleButton(module_id, label, icon)
                    
                    if module_id == self.active_module:
                        button.add_class("-active")
                    yield button
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle module button press."""
        if isinstance(event.button, ModuleButton):
            # Remove active class from all buttons
            for button in self.query(ModuleButton):
                button.remove_class("-active")
            
            # Add active class to pressed button
            event.button.add_class("-active")
            
            # Update active module
            self.active_module = event.button.module_id
            
            # Post message
            self.post_message(self.ModuleSelected(event.button.module_id))

