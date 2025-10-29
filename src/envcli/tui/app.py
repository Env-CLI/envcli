"""
Main EnvCLI TUI Application
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.binding import Binding
from textual.widgets import Static

from .components import Header, Sidebar, Footer
from .screens.dashboard import DashboardScreen
from .screens.variables import VariablesScreen
from .screens.profiles import ProfilesScreen
from .screens.ai_analysis import AIAnalysisScreen
from .screens.rules import RulesScreen
from .screens.encryption import EncryptionScreen
from .screens.cloud_sync import CloudSyncScreen
from .screens.kubernetes import KubernetesScreen
from .screens.rbac import RBACScreen
from .screens.compliance import ComplianceScreen
from .screens.audit import AuditScreen
from .screens.cicd import CICDScreen
from .screens.events import EventsScreen
from .screens.monitoring import MonitoringScreen
from .screens.plugins import PluginsScreen
from .screens.analytics import AnalyticsScreen
from .screens.predictive import PredictiveScreen
from .screens.settings import SettingsScreen
from .theme import TUI_CSS


class ContentPanel(Container):
    """Main content panel that displays active module."""
    
    DEFAULT_CSS = """
    ContentPanel {
        background: #0E141B;
        padding: 0;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.current_module = "dashboard"
    
    def compose(self) -> ComposeResult:
        """Compose initial content."""
        yield DashboardScreen()
    
    async def switch_module(self, module_id: str):
        """Switch to a different module."""
        self.current_module = module_id
        
        # Clear current content
        await self.query("*").remove()
        
        # Load new module
        if module_id == "dashboard":
            await self.mount(DashboardScreen())
        elif module_id == "variables":
            await self.mount(VariablesScreen(self.app.profile))
        elif module_id == "profiles":
            await self.mount(ProfilesScreen())
        elif module_id == "encryption":
            await self.mount(EncryptionScreen())
        elif module_id == "ai_analysis":
            await self.mount(AIAnalysisScreen())
        elif module_id == "rules":
            await self.mount(RulesScreen())
        elif module_id == "cloud_sync":
            await self.mount(CloudSyncScreen())
        elif module_id == "kubernetes":
            await self.mount(KubernetesScreen())
        elif module_id == "rbac":
            await self.mount(RBACScreen())
        elif module_id == "compliance":
            await self.mount(ComplianceScreen())
        elif module_id == "audit":
            await self.mount(AuditScreen())
        elif module_id == "cicd":
            await self.mount(CICDScreen())
        elif module_id == "events":
            await self.mount(EventsScreen())
        elif module_id == "monitoring":
            await self.mount(MonitoringScreen())
        elif module_id == "plugins":
            await self.mount(PluginsScreen())
        elif module_id == "analytics":
            await self.mount(AnalyticsScreen())
        elif module_id == "predict":
            await self.mount(PredictiveScreen())
        elif module_id == "settings":
            await self.mount(SettingsScreen())
        else:
            await self.mount(Static(f"Module '{module_id}' not found", classes="panel"))


class EnvCLIApp(App):
    """EnvCLI Terminal User Interface Application."""
    
    CSS = TUI_CSS
    
    TITLE = "EnvCLI v3.0.0"
    SUB_TITLE = "Enterprise Environment Management"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+d", "quit", "Quit", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+k", "quick_search", "Search", priority=True),
        Binding("/", "command_palette", "Commands", priority=True),
        Binding("?", "help", "Help", priority=True),
        Binding("ctrl+1", "switch_module('dashboard')", "Dashboard"),
        Binding("ctrl+2", "switch_module('variables')", "Variables"),
        Binding("ctrl+3", "switch_module('profiles')", "Profiles"),
        Binding("ctrl+4", "switch_module('ai_analysis')", "AI"),
    ]
    
    def __init__(self, profile: str = "default", ai_provider: str = "none"):
        super().__init__()
        self.profile = profile
        self.ai_provider = ai_provider
        self.content_panel = None
    
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(self.profile, self.ai_provider)
        yield Sidebar()
        self.content_panel = ContentPanel()
        yield self.content_panel
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the TUI on mount."""
        self.notify(
            "Welcome to EnvCLI! 🎉",
            title="EnvCLI",
            severity="information"
        )

    def on_sidebar_module_selected(self, message: Sidebar.ModuleSelected) -> None:
        """Handle module selection from sidebar."""
        if self.content_panel:
            self.run_worker(self.content_panel.switch_module(message.module_id))
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_quick_search(self) -> None:
        """Open quick search."""
        self.notify("Quick search (Ctrl+K) - Coming soon!", severity="information")
    
    def action_command_palette(self) -> None:
        """Open command palette."""
        self.notify("Command palette (/) - Coming soon!", severity="information")
    
    def action_help(self) -> None:
        """Show help."""
        self.notify("Help (?) - Coming soon!", severity="information")
    
    def action_switch_module(self, module_id: str) -> None:
        """Switch to a module via keyboard shortcut."""
        if self.content_panel:
            self.run_worker(self.content_panel.switch_module(module_id))


def run_tui(profile: str = "default", ai_provider: str = "none"):
    """Run the EnvCLI TUI application."""
    app = EnvCLIApp(profile=profile, ai_provider=ai_provider)
    app.run()


if __name__ == "__main__":
    run_tui()

