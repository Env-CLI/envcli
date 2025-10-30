"""
Main EnvCLI TUI Application
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.binding import Binding
from textual.widgets import Static, Input, Button
from textual.screen import ModalScreen

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
from .screens.login_prompt import LoginPromptScreen
from .theme import TUI_CSS
from .themes import ThemeManager, generate_css
from ..rbac import rbac_manager


class ContentPanel(Container):
    """Main content panel that displays active module."""

    DEFAULT_CSS = """
    ContentPanel {
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

    TITLE = "EnvCLI v3.0.0"
    SUB_TITLE = "Enterprise Environment Management"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+d", "quit", "Quit", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+k", "quick_search", "Search", priority=True),
        Binding("/", "command_palette", "Commands", priority=True),
        Binding("?", "help", "Help", priority=True),
        Binding("ctrl+0", "switch_module('settings')", "Settings"),
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

        # Initialize theme manager
        config_dir = Path.home() / ".envcli"
        self.theme_manager = ThemeManager(config_dir)

        # Set CSS from theme
        self.CSS = generate_css(self.theme_manager.get_colors())
    
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(self.profile, self.ai_provider)
        yield Sidebar()
        self.content_panel = ContentPanel()
        yield self.content_panel
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the TUI on mount."""
        # Check if RBAC is enabled and user is not logged in
        if rbac_manager.is_enabled():
            current_user = rbac_manager.get_current_user()
            if not current_user:
                # Schedule login prompt to run in a worker
                self.run_worker(self._show_login_prompt())
                return
            else:
                # User already logged in
                self.notify(
                    f"Welcome back, {current_user}! 🎉",
                    title="EnvCLI",
                    severity="information"
                )
        else:
            # RBAC not enabled
            self.notify(
                "Welcome to EnvCLI! 🎉",
                title="EnvCLI",
                severity="information"
            )

    async def _show_login_prompt(self) -> None:
        """Show login prompt in a worker context."""
        result = await self.push_screen_wait(LoginPromptScreen())
        if not result:
            # User cancelled login
            self.notify(
                "Login required. Exiting...",
                title="Authentication Required",
                severity="warning"
            )
            self.exit()
            return
        else:
            # User logged in successfully
            logged_in_user = rbac_manager.get_current_user()
            self.notify(
                f"Welcome, {logged_in_user}! 🎉",
                title="Login Successful",
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
        self.notify("Pushing quick search modal", severity="information")
        self.push_screen(QuickSearchModal())

    def action_command_palette(self) -> None:
        """Open command palette."""
        self.push_screen(CommandPaletteModal())

    def action_help(self) -> None:
        """Show help."""
        self.push_screen(HelpModal())
    
    def action_switch_module(self, module_id: str) -> None:
        """Switch to a module via keyboard shortcut."""
        if self.content_panel:
            self.run_worker(self.content_panel.switch_module(module_id))

    def reload_theme(self) -> None:
        """Reload the theme and apply it to all components."""
        # Reload theme manager
        self.theme_manager.load()
        colors = self.theme_manager.get_colors()

        # Generate new CSS
        new_css = generate_css(colors)

        # Update app CSS
        self.CSS = new_css
        self.refresh_css()

        # Refresh all widgets
        self.refresh(layout=True)

        # Update sidebar specifically
        try:
            sidebar = self.query_one("Sidebar")
            sidebar.update_css()
        except:
            pass


class HelpModal(ModalScreen):
    """Help modal showing keybindings and usage."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    HelpModal Container {
        width: 80;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 2;
    }

    .modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .info-label {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .help-item {
        margin-bottom: 0;
        color: $text;
    }

    .spacer {
        height: 1;
    }

    .close-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("🆘 Help & Keybindings", classes="modal-title")
            yield Static("Keyboard Shortcuts:", classes="info-label")
            yield Static("• Ctrl+1: Dashboard", classes="help-item")
            yield Static("• Ctrl+2: Variables", classes="help-item")
            yield Static("• Ctrl+3: Profiles", classes="help-item")
            yield Static("• Ctrl+4: AI Analysis", classes="help-item")
            yield Static("• Ctrl+K: Quick Search", classes="help-item")
            yield Static("• /: Command Palette", classes="help-item")
            yield Static("• ?: Help", classes="help-item")
            yield Static("• Q/Ctrl+C: Quit", classes="help-item")
            yield Static("", classes="spacer")
            yield Static("Navigation:", classes="info-label")
            yield Static("• Use arrow keys or mouse to navigate", classes="help-item")
            yield Static("• Enter/Space to select buttons", classes="help-item")
            yield Static("• Tab to cycle focus", classes="help-item")
            yield Static("", classes="spacer")
            yield Static("Press ESC to close", classes="close-hint")


class CommandPaletteModal(ModalScreen):
    """Command palette modal with common CLI commands."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    CommandPaletteModal {
        align: center middle;
    }

    CommandPaletteModal Container {
        width: 80;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 2;
    }

    .modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .info-label {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .cmd-item {
        margin-bottom: 0;
        color: $text;
    }

    .spacer {
        height: 1;
    }

    .note {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    .close-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("📋 Command Palette", classes="modal-title")
            yield Static("Common CLI Commands:", classes="info-label")
            yield Static("• env list: List all profiles", classes="cmd-item")
            yield Static("• env use <profile>: Switch to profile", classes="cmd-item")
            yield Static("• env set <key> <value>: Set variable", classes="cmd-item")
            yield Static("• env get <key>: Get variable value", classes="cmd-item")
            yield Static("• env delete <key>: Delete variable", classes="cmd-item")
            yield Static("• env export <profile>: Export profile", classes="cmd-item")
            yield Static("• env import <file>: Import profile", classes="cmd-item")
            yield Static("• env backup: Create backup", classes="cmd-item")
            yield Static("", classes="spacer")
            yield Static("Run these commands in terminal for CLI usage", classes="note")
            yield Static("Press ESC to close", classes="close-hint")


class QuickSearchModal(ModalScreen):
    """Quick search modal."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    QuickSearchModal {
        align: center middle;
    }

    QuickSearchModal Container {
        width: auto;
        height: auto;
        max-width: 80;
        max-height: 60;
        background: $surface;
        border: solid $primary;
        padding: 2;
    }

    .modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .search-input {
        margin-bottom: 1;
    }

    .results-area {
        height: 1fr;
        overflow-y: auto;
    }

    .result-item {
        margin-bottom: 1;
        padding: 1;
        border: solid $accent;
        background: $surface;
        color: #00FF00;
    }

    .no-results {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
    }

    .close-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.search_results = []
        # Debug
        # self.app.notify("Quick search modal opened", severity="information")  # Can't notify here, app not set yet

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("🔍 Quick Search", classes="modal-title")
            yield Input(placeholder="Search profiles, variables...", classes="search-input", id="search-input")
            yield Button("Search", id="search-btn")
            yield Button("Test Button", id="test-btn")
            with VerticalScroll(classes="results-area"):
                yield from self._render_results()

    def on_mount(self):
        self.app.notify("Quick search modal mounted", severity="information")
        # Focus the input
        self._focus_input()

    def _focus_input(self):
        input_widget = self.query_one("#search-input", Input)
        self.set_focus(input_widget)
        self.app.notify("Focused input", severity="information")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "search-btn":
            input_widget = self.query_one("#search-input", Input)
            query = input_widget.value.lower()
            self.app.notify(f"Searching for '{query}'", severity="information")
            self.search_results = self._perform_search(query)
            self.app.notify(f"Found {len(self.search_results)} results", severity="information")
            self._update_results()
        elif event.button.id == "test-btn":
            self.app.notify("Test button pressed", severity="information")

    def _perform_search(self, query: str):
        results = []
        from ..config import list_profiles
        from ..env_manager import EnvManager

        profiles = list_profiles()
        self.app.notify(f"Searching '{query}' in profiles: {profiles}", severity="information")

        # Search profiles
        for profile in profiles:
            if query in profile.lower():
                results.append({
                    "title": f"Profile: {profile}",
                    "detail": f"Switch to profile {profile}"
                })

        # Search variables
        for profile in profiles:
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                for key, value in env_vars.items():
                    if query in key.lower() or query in str(value).lower():
                        masked_value = self._mask_sensitive_value(key, value)
                        results.append({
                            "title": f"Variable: {key} in {profile}",
                            "detail": f"Value: {masked_value}"
                        })
            except:
                pass

        return results[:20]  # Limit to 20 results

    def _mask_sensitive_value(self, key: str, value: str) -> str:
        sensitive_keywords = ['secret', 'key', 'token', 'password', 'auth']
        if any(word in key.lower() for word in sensitive_keywords):
            return "*" * len(str(value))
        return str(value)

    def _update_results(self):
        self.app.notify(f"Updating results: {len(self.search_results)} results", severity="information")
        results_area = self.query_one(".results-area", VerticalScroll)
        results_area.query("*").remove()
        results_area.mount(*self._render_results())

    def _render_results(self):
        widgets = []
        if not self.search_results:
            widgets.append(Static("No results found", classes="no-results"))
        else:
            for result in self.search_results:
                widgets.append(ResultItem(result["title"], result["detail"]))
        widgets.append(Static("Press ESC to close", classes="close-hint"))
        return widgets


class ResultItem(Static):
    """A result item widget."""

    def __init__(self, title: str, detail: str):
        super().__init__(f"{title}\n{detail}", classes="result-item")

    def on_input_changed(self, event) -> None:
        self.app.notify(f"Input changed: '{event.value}' id={event.input.id}", severity="information")
        if event.input.id == "search-input":
            query = event.value.lower()
            self.app.notify(f"Processing query: '{query}'", severity="information")
            self.search_results = self._perform_search(query)
            self._update_results()

    def _perform_search(self, query: str):
        results = []
        from ..config import list_profiles
        from ..env_manager import EnvManager

        profiles = list_profiles()
        self.app.notify(f"Searching '{query}' in profiles: {profiles}", severity="information")

        # Search profiles
        for profile in profiles:
            if query in profile.lower():
                results.append({
                    "title": f"Profile: {profile}",
                    "detail": f"Switch to profile {profile}"
                })

        # Search variables
        for profile in list_profiles():
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                for key, value in env_vars.items():
                    if query in key.lower() or query in str(value).lower():
                        masked_value = self._mask_sensitive_value(key, value)
                        results.append({
                            "title": f"Variable: {key} in {profile}",
                            "detail": f"Value: {masked_value}"
                        })
            except:
                pass

        return results[:20]  # Limit to 20 results

    def _mask_sensitive_value(self, key: str, value: str) -> str:
        sensitive_keywords = ['secret', 'key', 'token', 'password', 'auth']
        if any(word in key.lower() for word in sensitive_keywords):
            return "*" * len(str(value))
        return str(value)

    def _update_results(self):
        self.app.notify(f"Updating results: {len(self.search_results)} results", severity="information")
        results_area = self.query_one(".results-area", VerticalScroll)
        results_area.query("*").remove()
        results_area.mount(*self._render_results())


def run_tui(profile: str = "default", ai_provider: str = "none"):
    """Run the EnvCLI TUI application."""
    app = EnvCLIApp(profile=profile, ai_provider=ai_provider)
    app.run()


if __name__ == "__main__":
    run_tui()

