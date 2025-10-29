"""
Sidebar navigation component for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static
from textual.message import Message
from ..theme import get_module_icon


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
    
    DEFAULT_CSS = """
    Sidebar {
        dock: left;
        width: 32;
        background: #0D1117;
        border-right: thick #00E676;
    }

    .sidebar-title {
        dock: top;
        height: 4;
        padding: 1 2;
        background: #00E676;
        color: #0D1117;
        text-style: bold;
        text-align: center;
    }

    .sidebar-scroll {
        height: 1fr;
        padding: 1 0;
    }

    ModuleButton {
        width: 100%;
        height: 3;
        background: transparent;
        color: #B0BEC5;
        border: none;
        border-left: thick transparent;
        text-align: left;
        padding: 0 3;
        margin: 0 0 0 0;
    }

    ModuleButton:hover {
        background: #161B22;
        color: #00E676;
        border-left: thick #00E676;
    }

    ModuleButton.-active {
        background: #1A2332;
        color: #00E676;
        border-left: thick #00E676;
        text-style: bold;
    }

    .module-separator {
        width: 100%;
        height: 1;
        padding: 0 2;
        margin: 1 0;
        color: #37474F;
        text-style: dim;
    }
    """
    
    class ModuleSelected(Message):
        """Message sent when a module is selected."""
        
        def __init__(self, module_id: str):
            super().__init__()
            self.module_id = module_id
    
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
                ("plugins", "Plugins"),
                ("settings", "Settings"),
            ]),
        ]
    
    def compose(self) -> ComposeResult:
        """Compose sidebar widgets."""
        yield Static("◆ ENVCLI", classes="sidebar-title")

        with VerticalScroll(classes="sidebar-scroll"):
            for group_name, modules in self.module_groups:
                # Add group separator
                yield ModuleSeparator(f"─ {group_name} ─")

                # Add modules in this group
                for module_id, label in modules:
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

