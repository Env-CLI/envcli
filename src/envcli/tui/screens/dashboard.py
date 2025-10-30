"""
Dashboard screen for EnvCLI TUI
"""

from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from ...env_manager import EnvManager
from ...config import get_current_profile, list_profiles
from ...ai_assistant import AIAssistant


class StatCard(Static):
    """A card displaying a statistic."""
    
    DEFAULT_CSS = """
    StatCard {
        background: #1A2332;
        border: solid #37474F;
        padding: 1;
        height: 7;
        width: 1fr;
        margin: 0 1;
    }
    """
    
    def __init__(self, label: str, value: str, icon: str = ""):
        super().__init__()
        self.label = label
        self.value = value
        self.icon = icon
    
    def render(self) -> Text:
        """Render the stat card."""
        text = Text()

        if self.icon:
            text.append(f"{self.icon}\n", style="#64FFDA")

        text.append(f"{self.value}\n", style="bold #00E676")
        text.append(self.label, style="#757575")

        text.justify = "center"
        return text


class AlertFeed(Static):
    """Feed of recent alerts and notifications."""

    DEFAULT_CSS = """
    AlertFeed {
        background: #1A2332;
        border: solid #37474F;
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, profile: str):
        super().__init__()
        self.profile = profile

    def render(self) -> Panel:
        """Render the alert feed."""
        from ...ai_actions import AIActionExecutor

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Icon", width=3)
        table.add_column("Message")
        table.add_column("Time", width=10)

        # Get real activity data
        alerts = []

        # Check for recent AI actions
        executor = AIActionExecutor(self.profile)
        history = executor.get_action_history(limit=3)
        for entry in history:
            action = entry.get("action", {})
            timestamp = entry.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_ago = self._time_ago(dt)
                    alerts.append(("+", f"[green]{action.get('description', 'Action applied')}[/green]", time_ago))
                except:
                    pass

        # Add profile info
        manager = EnvManager(self.profile)
        env_vars = manager.load_env()
        alerts.append(("vFO", f"[blue]Profile '{self.profile}' has {len(env_vars)} variables[/blue]", "now"))

        # Check for sensitive variables
        sensitive_count = sum(1 for k in env_vars.keys()
                            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
        if sensitive_count > 0:
            alerts.append(("[", f"[yellow]{sensitive_count} sensitive variables detected[/yellow]", "now"))

        # Fill with placeholder if not enough
        if len(alerts) == 0:
            alerts.append(("vFO", "[dim]No recent activity[/dim]", ""))

        for icon, message, time in alerts[:4]:  # Show max 4
            table.add_row(icon, message, f"[dim]{time}[/dim]")

        return Panel(
            table,
            title="[bold #00E676]Recent Activity[/bold #00E676]",
            border_style="#37474F"
        )

    def _time_ago(self, dt: datetime) -> str:
        """Calculate time ago string."""
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"


class QuickActions(Static):
    """Quick action buttons."""
    
    DEFAULT_CSS = """
    QuickActions {
        background: #1A2332;
        border: solid #37474F;
        padding: 1;
        height: auto;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose quick action buttons."""
        from textual.widgets import Label
        
        yield Label("[bold #00E676]Quick Actions[/bold #00E676]")
        
        with Horizontal():
            yield Button("* Run AI Analysis", id="btn_ai_analysis")
            yield Button("~ Sync to Cloud", id="btn_cloud_sync")
            yield Button("+ Check Compliance", id="btn_compliance")


class AIInsights(Static):
    """AI-powered insights panel."""

    DEFAULT_CSS = """
    AIInsights {
        background: #1A2332;
        border: solid #37474F;
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, profile: str):
        super().__init__()
        self.profile = profile

    def render(self) -> Panel:
        """Render AI insights."""
        text = Text()

        # Get real insights
        manager = EnvManager(self.profile)
        env_vars = manager.load_env()

        insights = []

        # Check for sensitive variables
        sensitive_vars = [k for k in env_vars.keys()
                         if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])]
        if sensitive_vars:
            non_uppercase = [k for k in sensitive_vars if not k.isupper()]
            if non_uppercase:
                insights.append(("!", f"{len(non_uppercase)} secrets not following uppercase convention", "#FFB300"))
            else:
                insights.append(("+", f"All {len(sensitive_vars)} secrets follow naming conventions", "#00E676"))

        # Check for naming patterns
        mixed_case = [k for k in env_vars.keys() if not k.isupper() and not k.islower()]
        if mixed_case:
            insights.append(("📝", f"{len(mixed_case)} variables could use better naming", "#2196F3"))

        # Check for duplicates or similar names
        if len(env_vars) > 0:
            insights.append(("=", f"Managing {len(env_vars)} environment variables", "#64FFDA"))

        # Check AI status
        assistant = AIAssistant()
        if assistant.enabled:
            insights.append(("*", "AI analysis available - run analysis for recommendations", "#00E676"))
        else:
            insights.append(("!", "AI features disabled - enable for smart recommendations", "#FFB300"))

        # Show insights
        if not insights:
            insights.append(("vFO", "No insights available", "#757575"))

        for icon, message, color in insights[:4]:  # Show max 4
            text.append(f"{icon} ", style=color)
            text.append(f"{message}\n", style="#E0E0E0")

        return Panel(
            text,
            title="[bold #00E676]AI Insights[/bold #00E676]",
            border_style="#37474F"
        )


class DashboardScreen(Container):
    """Main dashboard screen."""

    DEFAULT_CSS = """
    DashboardScreen {
        background: #0E141B;
        padding: 1 2;
    }

    .dashboard-title {
        dock: top;
        height: 3;
        padding: 1 0;
        color: #00E676;
        text-style: bold;
    }

    .stats-row {
        height: 9;
        margin: 1 0;
    }

    .content-row {
        height: 1fr;
        margin: 1 0;
    }

    .actions-row {
        height: 5;
        margin: 1 0;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.manager = EnvManager(self.current_profile)
        self.assistant = AIAssistant()

    def compose(self) -> ComposeResult:
        """Compose dashboard widgets."""
        yield Static("= Dashboard Overview", classes="dashboard-title")

        # Get real data
        env_vars = self.manager.load_env()
        total_vars = len(env_vars)
        profiles = list_profiles()
        total_profiles = len(profiles)

        # Count sensitive variables
        sensitive_count = sum(1 for k in env_vars.keys()
                            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))

        # Calculate compliance score (simple heuristic)
        compliance_score = 100
        if total_vars > 0:
            # Deduct points for issues
            if sensitive_count > 0:
                # Check if sensitive vars are uppercase
                uppercase_secrets = sum(1 for k in env_vars.keys()
                                      if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])
                                      and k.isupper())
                if uppercase_secrets < sensitive_count:
                    compliance_score -= 10

        # Stats row
        with Horizontal(classes="stats-row"):
            yield StatCard("Total Variables", str(total_vars), "T")
            yield StatCard("Active Profiles", str(total_profiles), "/")
            yield StatCard("Sensitive Vars", str(sensitive_count), "[")
            yield StatCard("Compliance Score", f"{compliance_score}%", "+")
        
        # Content row
        with Horizontal(classes="content-row"):
            with Vertical():
                yield AlertFeed(self.current_profile)
            with Vertical():
                yield AIInsights(self.current_profile)
        
        # Quick actions row
        with Horizontal(classes="actions-row"):
            yield QuickActions()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn_ai_analysis":
            self.app.notify("Running AI analysis...", severity="information")
        elif button_id == "btn_cloud_sync":
            self.app.notify("Syncing to cloud...", severity="information")
        elif button_id == "btn_compliance":
            self.app.notify("Checking compliance...", severity="information")

