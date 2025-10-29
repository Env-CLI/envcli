from pathlib import Path
from typing import List
import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from .config import get_current_profile, set_current_profile, list_profiles as list_profile_names, create_profile, list_hooks, add_hook, remove_hook, is_analytics_enabled, set_analytics_enabled, get_command_stats
from .env_manager import EnvManager
from .encryption import encrypt_file, decrypt_file
from .validation import validate_profile
from .hooks import execute_hooks
from .sync import get_sync_service
from .plugins import plugin_manager
from .tui_editor import edit_env_tui
from .shell_integration import setup_auto_loading, detect_shell, ShellIntegration
from .dashboard import show_dashboard
from .team_collaboration import TeamManager, setup_team_interactive
from .event_hooks import event_manager, trigger_env_changed, trigger_profile_created, trigger_sync_completed
from .telemetry import TelemetryAnalyzer
from .ai_assistant import AIAssistant
from .audit_reporting import AuditReporter
from .policy_engine import PolicyEngine
from .rbac import RBACManager, Role, Permission, rbac_manager
from .kubernetes_integration import KubernetesSecretSync, KubernetesConfigMapSync
from .azure_integration import AzureKeyVaultSync
from .gcp_integration import GCPSecretManagerSync
from .monitoring import MonitoringSystem
from .ci_cd_integration import CICDPipeline, EnvironmentPromotion
from .api_server import start_api_server
from .web_dashboard import run_web_dashboard
from .predictive_analytics import PredictiveAnalytics
from .compliance_frameworks import ComplianceFrameworkManager

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """EnvCLI - Manage environment variables across projects."""
    pass

# Local env management commands
env_app = typer.Typer()
app.add_typer(env_app, name="env", help="Manage environment variables")

@env_app.command("list")
def list_env(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to use"),
    mask: bool = typer.Option(True, "--mask/--no-mask", help="Mask secret values"),
):
    """List all environment variables in the current profile."""
    from .config import log_command
    log_command("env list")

    profile = profile or get_current_profile()
    manager = EnvManager(profile)
    env_vars = manager.list_env(mask=mask)

    if not env_vars:
        console.print(f"No environment variables in profile '{profile}'")
        return

    table = Table(title=f"Environment Variables - Profile: {profile}")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in sorted(env_vars.items()):
        table.add_row(key, value)

    console.print(table)

@env_app.command("add")
def add_env(
    key: str = typer.Argument(..., help="Environment variable key"),
    value: str = typer.Argument(..., help="Environment variable value"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Add or update an environment variable."""
    profile = profile or get_current_profile()
    manager = EnvManager(profile)
    manager.add_env(key, value)
    console.print(f"Added {key} to profile '{profile}'")

@env_app.command("remove")
def remove_env(
    key: str = typer.Argument(..., help="Environment variable key"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Remove an environment variable."""
    profile = profile or get_current_profile()
    manager = EnvManager(profile)
    manager.remove_env(key)
    console.print(f"Removed {key} from profile '{profile}'")

@env_app.command("edit")
def edit_env(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to use"),
):
    """Edit environment variables in a TUI editor."""
    profile = profile or get_current_profile()
    try:
        edit_env_tui(profile)
        console.print(f"[green]✓[/green] Environment variables saved for profile '{profile}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@env_app.command("diff")
def diff_env(
    profile1: str = typer.Argument(..., help="First profile"),
    profile2: str = typer.Argument(..., help="Second profile"),
):
    """Compare two environment profiles with enhanced colored output."""
    manager1 = EnvManager(profile1)
    diff_result = manager1.diff(profile2)

    console.print(f"[bold]🔍 Differences between '{profile1}' and '{profile2}':[/bold]\n")

    if diff_result["added"]:
        console.print("[bold green]➕ Added in {profile2}:[/bold green]")
        for k, v in diff_result["added"].items():
            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']):
                console.print(f"  [cyan]{k}[/cyan] = [red]***masked***[/red]")
            else:
                console.print(f"  [cyan]{k}[/cyan] = [green]{v}[/green]")
        console.print()

    if diff_result["removed"]:
        console.print("[bold red]➖ Removed in {profile2}:[/bold red]")
        for k, v in diff_result["removed"].items():
            if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']):
                console.print(f"  [cyan]{k}[/cyan] = [red]***masked***[/red]")
            else:
                console.print(f"  [cyan]{k}[/cyan] = [red]{v}[/red]")
        console.print()

    if diff_result["changed"]:
        console.print("[bold yellow]✏️  Changed:[/bold yellow]")
        for k, change in diff_result["changed"].items():
            console.print(f"  [cyan]{k}:[/cyan]")
            console.print(f"    [red]- {change['old']}[/red]")
            console.print(f"    [green]+ {change['new']}[/green]")
        console.print()

    if not any(diff_result.values()):
        console.print("[bold green]✅ No differences found.[/bold green]")

@env_app.command("import")
def import_env(
    file: str = typer.Argument(..., help="File to import from"),
    format: str = typer.Option("env", "--format", "-f", help="File format: env, json, yaml"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to import into"),
):
    """Import environment variables from a file."""
    profile = profile or get_current_profile()
    manager = EnvManager(profile)
    try:
        manager.load_from_file(file, format=format)
        console.print(f"Imported variables from {file} into profile '{profile}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@env_app.command("export")
def export_env(
    file: str = typer.Argument(..., help="File to export to"),
    format: str = typer.Option("env", "--format", "-f", help="File format: env, json, yaml, shell"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to export from"),
):
    """Export environment variables to a file."""
    profile = profile or get_current_profile()
    manager = EnvManager(profile)
    try:
        manager.export_to_file(file, format=format)
        console.print(f"Exported profile '{profile}' to {file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

# Project profile commands
profile_app = typer.Typer()
app.add_typer(profile_app, name="profile", help="Manage project profiles")

@profile_app.command("init")
def init_profile(
    name: str = typer.Option("dev", "--name", "-n", help="Profile name"),
    detect_env: bool = typer.Option(True, "--detect/--no-detect", help="Detect existing .env file"),
):
    """Initialize a profile for the current project."""
    try:
        create_profile(name)
        console.print(f"Created profile '{name}'")

        if detect_env:
            env_file = Path(".env")
            if env_file.exists():
                manager = EnvManager(name)
                manager.load_from_file(".env", format="env")
                console.print("Loaded variables from .env file")
            else:
                console.print("No .env file found to load")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")

@profile_app.command("use")
def use_profile(
    name: str = typer.Argument(..., help="Profile name"),
):
    """Switch to a different profile."""
    profiles = list_profile_names()
    if name not in profiles:
        console.print(f"[red]Error:[/red] Profile '{name}' does not exist. Available: {', '.join(profiles)}")
        return

    # Execute pre hooks
    execute_hooks("pre", "profile use")

    set_current_profile(name)
    console.print(f"Switched to profile '{name}'")

    # Execute post hooks
    execute_hooks("post", "profile use")

@profile_app.command("list")
def list_profiles_command():
    """List all available profiles."""
    profiles = list_profile_names()
    current = get_current_profile()

    if not profiles:
        console.print("No profiles found. Create one with 'envcli profile init'")
        return

    table = Table(title="Available Profiles")
    table.add_column("Profile", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Variables", style="yellow")

    for profile in profiles:
        status = "[bold green]active[/bold green]" if profile == current else ""
        manager = EnvManager(profile)
        var_count = len(manager.load_env())
        table.add_row(profile, status, str(var_count))

    console.print(table)

@profile_app.command("tree")
def tree_profiles():
    """Display profiles in a tree view."""
    profiles = list_profile_names()
    current = get_current_profile()

    if not profiles:
        console.print("No profiles found. Create one with 'envcli profile init'")
        return

    tree = Tree("📁 Environment Profiles", guide_style="bold bright_blue")

    for profile in sorted(profiles):
        manager = EnvManager(profile)
        env_vars = manager.load_env()

        # Profile node
        if profile == current:
            profile_node = tree.add(f"🔵 {profile} [active]")
        else:
            profile_node = tree.add(f"⚪ {profile}")

        # Environment variables
        for key, value in sorted(env_vars.items()):
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                display_value = '*' * len(value)
            else:
                display_value = value
            profile_node.add(f"{key} = {display_value}")

    console.print(tree)

# Encryption commands
encrypt_app = typer.Typer()
app.add_typer(encrypt_app, name="encrypt", help="Encrypt/decrypt environment files")

@encrypt_app.command("encrypt")
def encrypt_command(
    file: str = typer.Argument(..., help="File to encrypt"),
):
    """Encrypt an environment file."""
    try:
        encrypt_file(file)
        console.print(f"Encrypted {file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@encrypt_app.command("decrypt")
def decrypt_command(
    file: str = typer.Argument(..., help="File to decrypt"),
):
    """Decrypt an environment file."""
    try:
        decrypt_file(file)
        console.print(f"Decrypted {file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

# Hooks commands
hooks_app = typer.Typer()
app.add_typer(hooks_app, name="hooks", help="Manage command hooks")

@hooks_app.command("list")
def list_hooks_command():
    """List configured hooks."""
    hooks = list_hooks()
    if not hooks:
        console.print("No hooks configured")
        return

    table = Table(title="Configured Hooks")
    table.add_column("Type", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Hook Command", style="yellow")

    for i, hook in enumerate(hooks):
        table.add_row(hook["type"], hook["command"], hook["hook_command"])

    console.print(table)

@hooks_app.command("add")
def add_hooks_command(
    hook_type: str = typer.Argument(..., help="Hook type: pre or post"),
    command: str = typer.Argument(..., help="Command to hook (e.g., profile use)"),
    hook_command: str = typer.Argument(..., help="Command to execute"),
):
    """Add a hook."""
    if hook_type not in ["pre", "post"]:
        console.print("[red]Error:[/red] Hook type must be 'pre' or 'post'")
        raise typer.Exit(1)

    try:
        add_hook(hook_type, command, hook_command)
        console.print(f"Added {hook_type} hook for '{command}': {hook_command}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@hooks_app.command("remove")
def remove_hooks_command(
    index: int = typer.Argument(..., help="Hook index (from list)"),
):
    """Remove a hook by index."""
    try:
        remove_hook(index)
        console.print(f"Removed hook at index {index}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

# Analytics commands
analytics_app = typer.Typer()
app.add_typer(analytics_app, name="analytics", help="Usage analytics and tracking")

@analytics_app.command("enable")
def enable_analytics():
    """Enable usage tracking."""
    set_analytics_enabled(True)
    console.print("Analytics enabled")

@analytics_app.command("disable")
def disable_analytics():
    """Disable usage tracking."""
    set_analytics_enabled(False)
    console.print("Analytics disabled")

@analytics_app.command("stats")
def show_stats():
    """Show command usage statistics."""
    if not is_analytics_enabled():
        console.print("Analytics is disabled. Enable with 'envcli analytics enable'")
        return

    stats = get_command_stats()
    if not stats:
        console.print("No command history available")
        return

    table = Table(title="Command Usage Statistics")
    table.add_column("Command", style="cyan")
    table.add_column("Count", style="green")

    for cmd, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        table.add_row(cmd, str(count))

    console.print(table)

# Sync commands
sync_app = typer.Typer()
app.add_typer(sync_app, name="sync", help="Remote synchronization")

@sync_app.command("push")
def sync_push(
    service: str = typer.Argument(..., help="Sync service: aws_ssm, github_secrets, vault"),
    path: str = typer.Argument(..., help="Remote path/namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to push"),
):
    """Push profile to remote service."""
    profile = profile or get_current_profile()

    try:
        sync_service = get_sync_service(service)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pushing profile '{profile}' to {service}...", total=None)
            success = sync_service.push(profile, path)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pushed profile '{profile}' to {service}")
        else:
            console.print(f"[red]✗[/red] Failed to push profile '{profile}' to {service}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@sync_app.command("pull")
def sync_pull(
    service: str = typer.Argument(..., help="Sync service: aws_ssm, github_secrets, vault"),
    path: str = typer.Argument(..., help="Remote path/namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to pull into"),
):
    """Pull profile from remote service."""
    profile = profile or get_current_profile()

    try:
        sync_service = get_sync_service(service)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pulling from {service} to profile '{profile}'...", total=None)
            success = sync_service.pull(profile, path)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pulled into profile '{profile}' from {service}")
        else:
            console.print(f"[red]✗[/red] Failed to pull into profile '{profile}' from {service}")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@sync_app.command("status")
def sync_status(
    service: str = typer.Argument(..., help="Sync service: aws_ssm, github_secrets, vault"),
    path: str = typer.Argument(..., help="Remote path/namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to check"),
):
    """Show sync status between local and remote."""
    profile = profile or get_current_profile()

    try:
        sync_service = get_sync_service(service)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Checking sync status for '{profile}'...", total=None)
            status = sync_service.status(profile, path)
            progress.update(task, completed=True)

        if "error" in status:
            console.print(f"[red]Error:[/red] {status['error']}")
            raise typer.Exit(1)

        table = Table(title=f"Sync Status - {service}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        for key, value in status.items():
            table.add_row(key.replace("_", " ").title(), value)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Plugin commands
plugin_app = typer.Typer()
app.add_typer(plugin_app, name="plugin", help="Plugin management")

@plugin_app.command("list")
def list_plugins():
    """List installed plugins."""
    plugins = plugin_manager.list_plugins()
    if not plugins:
        console.print("No plugins installed")
        return

    table = Table(title="Installed Plugins")
    table.add_column("Plugin", style="cyan")
    table.add_column("Status", style="green")

    for plugin in plugins:
        table.add_row(plugin, "loaded")

    console.print(table)

@plugin_app.command("install")
def install_plugin(
    path: str = typer.Argument(..., help="Path to plugin file"),
):
    """Install a plugin from file."""
    try:
        plugin_manager.install_plugin(path)
        console.print(f"[green]✓[/green] Plugin installed successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@plugin_app.command("remove")
def remove_plugin(
    name: str = typer.Argument(..., help="Plugin name"),
):
    """Remove a plugin."""
    try:
        plugin_manager.remove_plugin(name)
        console.print(f"[green]✓[/green] Plugin removed successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command("validate")
def validate_command(
    schema_file: str = typer.Argument(..., help="Schema file (JSON/YAML)"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to validate"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation mode"),
):
    """Validate environment variables against a schema."""
    profile = profile or get_current_profile()
    try:
        errors = validate_profile(profile, schema_file, strict)
        if errors:
            console.print(f"[red]Validation failed for profile '{profile}':[/red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(1)
        else:
            console.print(f"[green]✓[/green] Profile '{profile}' validates successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Load plugins at startup
plugin_manager.load_plugins()
plugin_commands = plugin_manager.commands

@app.command("run-plugin")
def run_plugin_command(
    command: str = typer.Argument(..., help="Plugin command to run"),
    args: List[str] = typer.Argument(None, help="Arguments for the command"),
):
    """Run a plugin command."""
    if command in plugin_commands:
        try:
            # For simplicity, just call with basic args
            if args:
                plugin_commands[command](*args)
            else:
                plugin_commands[command]()
        except Exception as e:
            console.print(f"[red]Plugin command failed:[/red] {e}")
    else:
        console.print(f"[red]Plugin command not found:[/red] {command}")
        console.print(f"Available: {', '.join(plugin_commands.keys())}")

# Shell integration commands
shell_app = typer.Typer()
app.add_typer(shell_app, name="shell", help="Shell integration and auto-loading")

@shell_app.command("detect")
def detect_shell_command():
    """Detect the current shell type."""
    shell = detect_shell()
    console.print(f"Detected shell: {shell}")

@shell_app.command("auto-load")
def setup_auto_load(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to auto-load"),
    use_direnv: bool = typer.Option(False, "--direnv", help="Use direnv integration"),
):
    """Set up automatic environment loading."""
    profile = profile or get_current_profile()
    try:
        result = setup_auto_loading(profile, use_direnv)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@shell_app.command("load-shell")
def load_shell_command(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to load"),
):
    """Load environment variables into current shell."""
    profile = profile or get_current_profile()
    integration = ShellIntegration()
    commands = integration.inject_into_shell(profile)
    console.print(commands)

# TUI command
@app.command("tui")
def tui_command(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to use"),
    ai_provider: str = typer.Option(None, "--ai-provider", help="AI provider to use"),
):
    """Launch the EnvCLI Terminal User Interface (TUI)."""
    try:
        from .tui.app import run_tui

        # Get current profile if not specified
        if not profile:
            profile = get_current_profile()

        # Get AI provider if not specified
        if not ai_provider:
            from .config import load_config
            config = load_config()
            ai_provider = config.get("ai", {}).get("provider", "none")

        console.print(f"[green]Launching EnvCLI TUI...[/green]")
        console.print(f"[dim]Profile: {profile}[/dim]")
        console.print(f"[dim]AI Provider: {ai_provider}[/dim]")
        console.print()

        run_tui(profile=profile, ai_provider=ai_provider)
    except ImportError:
        console.print("[red]Error: Textual not installed. Install with:[/red]")
        console.print("[yellow]pip install textual[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error launching TUI: {e}[/red]")
        raise typer.Exit(1)

# Dashboard command
@app.command("dashboard")
def dashboard_command():
    """Launch the visual EnvCLI dashboard."""
    try:
        show_dashboard()
    except Exception as e:
        console.print(f"[red]Error launching dashboard:[/red] {e}")
        raise typer.Exit(1)

# Team collaboration commands
team_app = typer.Typer()
app.add_typer(team_app, name="team", help="Team collaboration features")

@team_app.command("create")
def create_team(
    name: str = typer.Argument(..., help="Team name"),
    admin: str = typer.Option("admin", "--admin", "-a", help="Admin username"),
):
    """Create a new team."""
    try:
        manager = TeamManager()
        result = manager.create_team(name, admin)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@team_app.command("join")
def join_team(
    name: str = typer.Argument(..., help="Team name"),
    user: str = typer.Option("user", "--user", "-u", help="Your username"),
):
    """Join an existing team."""
    try:
        manager = TeamManager()
        result = manager.join_team(name, user)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@team_app.command("setup")
def setup_team():
    """Interactive team setup wizard."""
    try:
        setup_team_interactive()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@team_app.command("create-profile")
def create_team_profile(
    name: str = typer.Argument(..., help="Shared profile name"),
    source: str = typer.Option(None, "--source", "-s", help="Source profile to copy from"),
):
    """Create a shared team profile."""
    try:
        manager = TeamManager()
        result = manager.create_shared_profile(name, source)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@team_app.command("list-profiles")
def list_team_profiles():
    """List shared team profiles."""
    try:
        manager = TeamManager()
        profiles = manager.list_shared_profiles()
        if profiles:
            console.print("Shared team profiles:")
            for profile in profiles:
                console.print(f"  • {profile}")
        else:
            console.print("No shared team profiles found.")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Event hooks commands
events_app = typer.Typer()
app.add_typer(events_app, name="events", help="Event-driven hooks")

@events_app.command("add-webhook")
def add_webhook(
    event: str = typer.Argument(..., help="Event type: env_changed, profile_created, sync_completed, validation_failed"),
    url: str = typer.Argument(..., help="Webhook URL"),
    method: str = typer.Option("POST", "--method", "-m", help="HTTP method"),
):
    """Add a webhook for an event."""
    try:
        config = {
            "url": url,
            "method": method,
            "headers": {"Content-Type": "application/json"}
        }
        result = event_manager.add_hook(event, "webhook", config)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@events_app.command("add-script")
def add_script_hook(
    event: str = typer.Argument(..., help="Event type"),
    script_path: str = typer.Argument(..., help="Path to script"),
):
    """Add a script hook for an event."""
    try:
        config = {
            "path": script_path,
            "timeout": 30
        }
        result = event_manager.add_hook(event, "script", config)
        console.print(f"[green]✓[/green] {result}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@events_app.command("list")
def list_event_hooks():
    """List all event hooks."""
    hooks = event_manager.list_hooks()
    if not hooks:
        console.print("No event hooks configured.")
        return

    for event, event_hooks in hooks.items():
        if event_hooks:
            console.print(f"[bold]{event}:[/bold]")
            for i, hook in enumerate(event_hooks):
                enabled = "✓" if hook.get("enabled", True) else "✗"
                console.print(f"  {enabled} [{hook['type']}] {hook['config']}")
            console.print()

# Telemetry and insights commands
insights_app = typer.Typer()
app.add_typer(insights_app, name="insights", help="Telemetry and insights")

@insights_app.command("analyze")
def analyze_insights():
    """Analyze environment variables and provide insights."""
    try:
        analyzer = TelemetryAnalyzer()
        report = analyzer.generate_report()

        console.print(f"[bold]📊 EnvCLI Insights Report[/bold]")
        console.print(f"Generated: {report['generated_at']}")
        console.print(f"Total insights: {report['summary']['total_insights']}")
        console.print()

        if report["insights"]:
            # Group by severity
            by_severity = {}
            for insight in report["insights"]:
                severity = insight["severity"]
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(insight)

            severity_order = ["error", "warning", "info", "suggestion"]
            for severity in severity_order:
                if severity in by_severity:
                    insights = by_severity[severity]
                    emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "suggestion": "💡"}.get(severity, "•")
                    console.print(f"[bold]{emoji} {severity.title()} ({len(insights)}):[/bold]")

                    for insight in insights[:5]:  # Show first 5
                        console.print(f"  • {insight['message']}")

                    if len(insights) > 5:
                        console.print(f"  • ... and {len(insights) - 5} more")
                    console.print()
        else:
            console.print("[green]✅ No insights found - your environments look good![/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@insights_app.command("summary")
def insights_summary():
    """Get a quick insights summary."""
    try:
        analyzer = TelemetryAnalyzer()
        summary = analyzer.get_insights_summary()
        console.print(summary)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# AI Assistant commands
ai_app = typer.Typer()
app.add_typer(ai_app, name="ai", help="AI-assisted analysis and recommendations")

@ai_app.command("enable")
def enable_ai(
    provider: str = typer.Option("pattern-matching", "--provider", "-p", help="AI provider (openai, anthropic, google, ollama, pattern-matching)"),
    model: str = typer.Option(None, "--model", "-m", help="Model name (optional)")
):
    """Enable AI features for metadata analysis."""
    try:
        ai = AIAssistant()
        ai.enable_ai(provider=provider, model=model)
        console.print("[green]✓[/green] AI features enabled")
        console.print(f"[dim]Provider: {provider}{f' ({model})' if model else ''}[/dim]")
        console.print("[dim]Note: AI only analyzes metadata, never raw secrets[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("disable")
def disable_ai():
    """Disable AI features."""
    try:
        ai = AIAssistant()
        ai.disable_ai()
        console.print("[green]✓[/green] AI features disabled")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("config")
def ai_config(
    provider: str = typer.Option(None, "--provider", "-p", help="Set AI provider (openai, anthropic, google, ollama, pattern-matching)"),
    model: str = typer.Option(None, "--model", "-m", help="Set model name"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration")
):
    """Configure AI provider settings."""
    try:
        ai = AIAssistant()

        if show or (not provider and not model):
            # Show current configuration
            status = ai.get_provider_status()

            console.print("[bold]🤖 AI Configuration[/bold]")
            console.print()
            console.print(f"Status: {'[green]Enabled[/green]' if status['enabled'] else '[red]Disabled[/red]'}")
            console.print(f"Current Provider: [cyan]{status['current_provider']}[/cyan]")
            if status['current_model']:
                console.print(f"Current Model: [cyan]{status['current_model']}[/cyan]")
            console.print()

            console.print("[bold]Available Providers:[/bold]")
            for p in status['providers']:
                status_icon = "✓" if p['available'] else "✗"
                status_color = "green" if p['available'] else "red"
                current_marker = " [cyan](current)[/cyan]" if p['current'] else ""
                console.print(f"  [{status_color}]{status_icon}[/{status_color}] {p['name']}: {p['display_name']}{current_marker}")

            # Show Ollama models if available
            try:
                from .ai_providers import OllamaProvider
                ollama = OllamaProvider()
                models = ollama.get_available_models()
                if models:
                    console.print()
                    console.print("[bold]📦 Ollama Models Available:[/bold]")
                    for model in models[:10]:  # Show first 10
                        console.print(f"  • {model}")
                    if len(models) > 10:
                        console.print(f"  [dim]... and {len(models) - 10} more[/dim]")
                    console.print()
                    console.print("[dim]Use with: envcli ai config --provider ollama --model <model>[/dim]")
            except:
                pass

            console.print()
            console.print("[dim]To configure a provider:[/dim]")
            console.print("[dim]  envcli ai config --provider openai[/dim]")
            console.print("[dim]  envcli ai config --provider anthropic --model claude-3-5-sonnet-20241022[/dim]")
            console.print("[dim]  envcli ai config --provider ollama  # Auto-detects best model[/dim]")
            console.print()
            console.print("[dim]Required environment variables:[/dim]")
            console.print("[dim]  OpenAI: OPENAI_API_KEY[/dim]")
            console.print("[dim]  Anthropic: ANTHROPIC_API_KEY[/dim]")
            console.print("[dim]  Google: GOOGLE_API_KEY[/dim]")
            console.print("[dim]  Ollama: Running locally (ollama serve)[/dim]")

        elif provider:
            # Configure provider
            result = ai.configure_provider(provider, model)

            if result['success']:
                console.print(f"[green]✓[/green] {result['message']}")
                console.print(f"[dim]Provider: {result['provider_name']}[/dim]")
            else:
                console.print(f"[red]✗[/red] {result['message']}")
                console.print(f"[yellow]Tip:[/yellow] Make sure the provider is properly configured")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("analyze")
def ai_analyze(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to analyze"),
):
    """Generate AI recommendations for environment variables."""
    profile = profile or get_current_profile()
    try:
        ai = AIAssistant()
        recommendations = ai.generate_recommendations(profile)

        if "error" in recommendations:
            console.print(f"[red]Error:[/red] {recommendations['error']}")
            raise typer.Exit(1)

        console.print(f"[bold]🤖 AI Analysis for Profile '{profile}'[/bold]")
        console.print(f"[dim]Provider: {recommendations.get('provider', 'Unknown')}[/dim]")
        console.print()

        # Show pattern-based analysis
        if recommendations.get("pattern_analysis"):
            console.print("[bold]📝 Pattern Analysis:[/bold]")
            for rec in recommendations["pattern_analysis"][:5]:  # Show first 5
                emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(rec["severity"], "•")
                console.print(f"  {emoji} {rec['message']}")
                if rec.get("suggestion"):
                    console.print(f"    💡 {rec['suggestion']}")
                console.print()
            if len(recommendations["pattern_analysis"]) > 5:
                console.print(f"  ... and {len(recommendations['pattern_analysis']) - 5} more")
            console.print()

        # Show AI-powered analysis if available
        if recommendations.get("ai_analysis"):
            console.print("[bold]🧠 AI-Powered Analysis:[/bold]")
            console.print()
            from rich.markdown import Markdown
            console.print(Markdown(recommendations["ai_analysis"]))
            console.print()

        if not recommendations.get("pattern_analysis") and not recommendations.get("ai_analysis"):
            console.print("[green]✅ No issues found - your variables follow best practices![/green]")
            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("suggest")
def ai_suggest(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to analyze"),
):
    """Generate actionable suggestions that can be applied automatically."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        console.print(f"[bold]🔍 Analyzing profile '{profile}' for improvements...[/bold]")
        console.print()

        executor = AIActionExecutor(profile)

        # Get AI recommendations first
        ai = AIAssistant()
        recommendations = ai.generate_recommendations(profile)

        # Parse into actionable items
        actions = executor.parse_recommendations(
            recommendations.get("ai_analysis", "") or ""
        )

        if not actions:
            console.print("[green]✅ No automatic improvements suggested![/green]")
            console.print("[dim]Your environment variables are well-organized.[/dim]")
            return

        console.print(f"[bold]💡 Found {len(actions)} actionable suggestion(s):[/bold]")
        console.print()

        for i, action in enumerate(actions, 1):
            console.print(f"[cyan]{i}.[/cyan] {action.description}")
            console.print(f"   [dim]Type: {action.action_type}[/dim]")
            if action.details.get("reason"):
                console.print(f"   [dim]Reason: {action.details['reason']}[/dim]")
            console.print()

        console.print("[yellow]💡 Tip:[/yellow] Use [cyan]envcli ai apply --preview[/cyan] to see changes before applying")
        console.print("[yellow]💡 Tip:[/yellow] Use [cyan]envcli ai apply[/cyan] to apply all suggestions")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)

@ai_app.command("apply")
def ai_apply(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to modify"),
    preview: bool = typer.Option(False, "--preview", help="Preview changes without applying"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Apply AI-suggested improvements to environment variables."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        executor = AIActionExecutor(profile)

        # Get AI recommendations
        ai = AIAssistant()
        recommendations = ai.generate_recommendations(profile)

        # Parse into actionable items
        actions = executor.parse_recommendations(
            recommendations.get("ai_analysis", "") or ""
        )

        if not actions:
            console.print("[green]✅ No improvements to apply![/green]")
            return

        console.print(f"[bold]🔧 Applying {len(actions)} improvement(s) to profile '{profile}'[/bold]")
        console.print()

        if preview:
            console.print("[yellow]📋 Preview Mode - No changes will be made[/yellow]")
            console.print()

        # Show what will be changed
        for i, action in enumerate(actions, 1):
            console.print(f"[cyan]{i}.[/cyan] {action.description}")

            if action.action_type in ["rename", "add_prefix"]:
                old_name = action.details["old_name"]
                new_name = action.details["new_name"]
                console.print(f"   [red]- {old_name}[/red]")
                console.print(f"   [green]+ {new_name}[/green]")
                console.print(f"   [dim]Value: [PRESERVED - NOT SHOWN][/dim]")

            console.print()

        if preview:
            console.print("[green]✓[/green] Preview complete. Use [cyan]envcli ai apply[/cyan] to apply changes.")
            return

        # Confirm before applying
        if not yes:
            console.print("[yellow]⚠️  This will modify your environment variables.[/yellow]")
            console.print("[yellow]⚠️  Values will be preserved, only names will change.[/yellow]")
            console.print()

            confirm = typer.confirm("Do you want to continue?")
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                return

        # Apply changes
        console.print()
        console.print("[bold]Applying changes...[/bold]")
        console.print()

        result = executor.apply_all_actions(dry_run=False)

        # Show results
        if result["successful"] > 0:
            console.print(f"[green]✓[/green] Successfully applied {result['successful']} change(s)")

        if result["failed"] > 0:
            console.print(f"[red]✗[/red] Failed to apply {result['failed']} change(s)")
            console.print()
            console.print("[bold]Failed actions:[/bold]")
            for res in result["results"]:
                if not res["success"]:
                    console.print(f"  [red]✗[/red] {res['message']}")

        console.print()
        console.print("[dim]💡 Changes have been logged for audit purposes[/dim]")
        console.print("[dim]💡 Use 'envcli ai history' to see all applied changes[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)

@ai_app.command("history")
def ai_history(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to show history for"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries to show"),
):
    """Show history of AI-applied changes."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        executor = AIActionExecutor(profile)
        history = executor.get_action_history(limit=limit)

        if not history:
            console.print(f"[dim]No AI actions have been applied to profile '{profile}'[/dim]")
            return

        console.print(f"[bold]📜 AI Action History for '{profile}'[/bold]")
        console.print(f"[dim]Showing last {len(history)} action(s)[/dim]")
        console.print()

        for entry in history:
            action = entry["action"]
            timestamp = entry["timestamp"]

            console.print(f"[cyan]•[/cyan] {action['description']}")
            console.print(f"  [dim]Applied: {timestamp}[/dim]")
            console.print(f"  [dim]Type: {action['action_type']}[/dim]")
            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("add-rule")
def ai_add_rule(
    rule_type: str = typer.Argument(..., help="Rule type: naming, prefix, transform, exclude"),
    pattern: str = typer.Argument(..., help="Regex pattern to match variable names"),
    target: str = typer.Argument(..., help="Target format/prefix/transformation"),
    description: str = typer.Option("", "--description", "-d", help="Rule description"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to apply rule to"),
):
    """Add a custom AI action rule."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        executor = AIActionExecutor(profile)

        if rule_type == "naming":
            executor.add_naming_rule(pattern, target, description)
            console.print(f"[green]✓[/green] Added naming rule: {pattern} → {target}")
        elif rule_type == "prefix":
            executor.add_prefix_rule(pattern, target, description)
            console.print(f"[green]✓[/green] Added prefix rule: {pattern} → {target}_*")
        elif rule_type == "transform":
            executor.add_transformation_rule(pattern, target, description)
            console.print(f"[green]✓[/green] Added transformation rule: {pattern} → {target}")
        elif rule_type == "exclude":
            executor.add_exclusion(pattern, description or target)
            console.print(f"[green]✓[/green] Added exclusion: {pattern}")
        else:
            console.print(f"[red]Error:[/red] Unknown rule type: {rule_type}")
            console.print("[dim]Valid types: naming, prefix, transform, exclude[/dim]")
            raise typer.Exit(1)

        console.print()
        console.print("[dim]💡 Run 'envcli ai suggest' to see rules in action[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)

@ai_app.command("list-rules")
def ai_list_rules(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to show rules for"),
):
    """List all custom AI action rules."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        executor = AIActionExecutor(profile)
        rules = executor.list_custom_rules()

        if not rules.get("enabled", True):
            console.print("[yellow]⚠️  Custom rules are disabled[/yellow]")
            console.print()

        total_rules = (
            len(rules.get("naming_rules", [])) +
            len(rules.get("prefix_rules", [])) +
            len(rules.get("transformation_rules", [])) +
            len(rules.get("exclusions", []))
        )

        if total_rules == 0:
            console.print("[dim]No custom rules defined[/dim]")
            console.print()
            console.print("[bold]Add rules with:[/bold]")
            console.print("  envcli ai add-rule naming '.*_key$' uppercase 'Uppercase all keys'")
            console.print("  envcli ai add-rule prefix 'redis_.*' 'REDIS_' 'Group Redis vars'")
            console.print("  envcli ai add-rule exclude 'PATH|HOME' 'System variables'")
            return

        console.print(f"[bold]📋 Custom AI Rules for '{profile}'[/bold]")
        console.print(f"[dim]Total: {total_rules} rule(s)[/dim]")
        console.print()

        # Naming rules
        if rules.get("naming_rules"):
            console.print("[bold cyan]Naming Rules:[/bold cyan]")
            for i, rule in enumerate(rules["naming_rules"]):
                console.print(f"  {i}. Pattern: [yellow]{rule['pattern']}[/yellow] → {rule['target_format']}")
                if rule.get("description"):
                    console.print(f"     [dim]{rule['description']}[/dim]")
            console.print()

        # Prefix rules
        if rules.get("prefix_rules"):
            console.print("[bold cyan]Prefix Rules:[/bold cyan]")
            for i, rule in enumerate(rules["prefix_rules"]):
                console.print(f"  {i}. Pattern: [yellow]{rule['pattern']}[/yellow] → {rule['prefix']}_*")
                if rule.get("description"):
                    console.print(f"     [dim]{rule['description']}[/dim]")
            console.print()

        # Transformation rules
        if rules.get("transformation_rules"):
            console.print("[bold cyan]Transformation Rules:[/bold cyan]")
            for i, rule in enumerate(rules["transformation_rules"]):
                console.print(f"  {i}. Pattern: [yellow]{rule['pattern']}[/yellow] → {rule['transformation']}")
                if rule.get("description"):
                    console.print(f"     [dim]{rule['description']}[/dim]")
            console.print()

        # Exclusions
        if rules.get("exclusions"):
            console.print("[bold cyan]Exclusions:[/bold cyan]")
            for i, exclusion in enumerate(rules["exclusions"]):
                console.print(f"  {i}. Pattern: [yellow]{exclusion['pattern']}[/yellow]")
                if exclusion.get("description"):
                    console.print(f"     [dim]{exclusion['description']}[/dim]")
            console.print()

        console.print("[dim]💡 Remove rules with: envcli ai remove-rule <type> <index>[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ai_app.command("remove-rule")
def ai_remove_rule(
    rule_type: str = typer.Argument(..., help="Rule type: naming_rules, prefix_rules, transformation_rules, exclusions"),
    index: int = typer.Argument(..., help="Index of rule to remove"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile"),
):
    """Remove a custom AI action rule."""
    profile = profile or get_current_profile()
    try:
        from .ai_actions import AIActionExecutor

        executor = AIActionExecutor(profile)

        if executor.remove_rule(rule_type, index):
            console.print(f"[green]✓[/green] Removed rule {index} from {rule_type}")
        else:
            console.print(f"[red]✗[/red] Rule not found: {rule_type}[{index}]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Audit Reporting commands
audit_app = typer.Typer()
app.add_typer(audit_app, name="audit", help="Compliance audit reports")

@audit_app.command("report")
def generate_audit_report(
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, csv, pdf"),
    days: int = typer.Option(30, "--days", "-d", help="Days to include in report"),
):
    """Generate compliance audit report."""
    try:
        reporter = AuditReporter()
        output_path = reporter.generate_compliance_report(format, days)
        console.print(f"[green]✓[/green] Audit report generated: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@audit_app.command("governance")
def governance_report(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to analyze"),
):
    """Generate governance report for a profile."""
    profile = profile or get_current_profile()
    try:
        reporter = AuditReporter()
        report = reporter.generate_governance_report(profile)

        console.print(f"[bold]📋 Governance Report for '{profile}'[/bold]")
        console.print(f"Governance Score: [bold]{report['governance_score']}%[/bold]")
        console.print()

        if report["insights"]:
            console.print("[bold]Key Insights:[/bold]")
            for insight in report["insights"][:5]:
                emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(insight.get("severity"), "•")
                console.print(f"  {emoji} {insight.get('message', 'Unknown insight')}")
            console.print()

        if report["recommendations"]:
            console.print("[bold]Recommendations:[/bold]")
            for rec in report["recommendations"]:
                console.print(f"  • {rec}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Policy Engine commands
policy_app = typer.Typer()
app.add_typer(policy_app, name="policy", help="Policy management and enforcement")

@policy_app.command("add-required")
def add_required_key(
    pattern: str = typer.Argument(..., help="Regex pattern for required keys"),
    description: str = typer.Option("", "--description", "-d", help="Policy description"),
):
    """Add a required key policy."""
    try:
        engine = PolicyEngine()
        engine.add_required_key_policy(pattern, description)
        console.print(f"[green]✓[/green] Required key policy added: {pattern}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@policy_app.command("add-prohibited")
def add_prohibited_pattern(
    pattern: str = typer.Argument(..., help="Regex pattern to prohibit"),
    description: str = typer.Option("", "--description", "-d", help="Policy description"),
):
    """Add a prohibited pattern policy."""
    try:
        engine = PolicyEngine()
        engine.add_prohibited_pattern_policy(pattern, description)
        console.print(f"[green]✓[/green] Prohibited pattern policy added: {pattern}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@policy_app.command("add-naming")
def add_naming_convention(
    convention: str = typer.Argument(..., help="Naming convention: uppercase, snake_case"),
    description: str = typer.Option("", "--description", "-d", help="Policy description"),
):
    """Add a naming convention policy."""
    try:
        engine = PolicyEngine()
        engine.add_naming_convention_policy(convention, description)
        console.print(f"[green]✓[/green] Naming convention policy added: {convention}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@policy_app.command("set-rotation")
def set_key_rotation(
    days: int = typer.Argument(..., help="Days between key rotations"),
):
    """Set key rotation schedule."""
    try:
        engine = PolicyEngine()
        engine.set_key_rotation_schedule(days)
        console.print(f"[green]✓[/green] Key rotation schedule set to {days} days")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@policy_app.command("validate")
def validate_policies(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to validate"),
):
    """Validate a profile against policies."""
    profile = profile or get_current_profile()
    try:
        engine = PolicyEngine()
        result = engine.validate_profile(profile)

        if result["valid"]:
            console.print(f"[green]✓[/green] Profile '{profile}' passes all policy checks")
        else:
            console.print(f"[red]✗[/red] Profile '{profile}' violates {len(result['violations'])} policies:")
            for violation in result["violations"]:
                severity_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(violation.get("severity"), "•")
                console.print(f"  {severity_emoji} {violation['message']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@policy_app.command("summary")
def policy_summary():
    """Show policy summary."""
    try:
        engine = PolicyEngine()
        summary = engine.get_policy_summary()

        console.print("[bold]📋 Policy Summary[/bold]")
        console.print(f"Enabled: {'Yes' if summary['enabled'] else 'No'}")
        console.print(f"Required Keys: {summary['required_keys_count']}")
        console.print(f"Prohibited Patterns: {summary['prohibited_patterns_count']}")
        console.print(f"Naming Conventions: {summary['naming_conventions_count']}")
        console.print(f"Key Rotation: {'Enabled' if summary['key_rotation_enabled'] else 'Disabled'}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# RBAC commands
rbac_app = typer.Typer()
app.add_typer(rbac_app, name="rbac", help="Role-based access control")

@rbac_app.command("enable")
def enable_rbac():
    """Enable role-based access control."""
    try:
        rbac_manager.enable_rbac()
        console.print("[green]✓[/green] RBAC enabled")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@rbac_app.command("disable")
def disable_rbac():
    """Disable role-based access control."""
    try:
        rbac_manager.disable_rbac()
        console.print("[green]✓[/green] RBAC disabled")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@rbac_app.command("add-user")
def add_rbac_user(
    username: str = typer.Argument(..., help="Username to add"),
    role: str = typer.Argument(..., help="Role: admin, member, guest"),
    added_by: str = typer.Option("admin", "--by", help="User performing the action"),
):
    """Add a user with a specific role."""
    try:
        role_enum = Role(role.lower())
        rbac_manager.add_user(username, role_enum, added_by)
        console.print(f"[green]✓[/green] User '{username}' added with role '{role}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@rbac_app.command("change-role")
def change_user_role(
    username: str = typer.Argument(..., help="Username"),
    role: str = typer.Argument(..., help="New role: admin, member, guest"),
    changed_by: str = typer.Option("admin", "--by", help="User performing the action"),
):
    """Change a user's role."""
    try:
        role_enum = Role(role.lower())
        rbac_manager.change_user_role(username, role_enum, changed_by)
        console.print(f"[green]✓[/green] User '{username}' role changed to '{role}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@rbac_app.command("list-users")
def list_rbac_users():
    """List all users and their roles."""
    try:
        users = rbac_manager.list_users()
        if users:
            console.print("[bold]👥 RBAC Users[/bold]")
            for user in users:
                console.print(f"  {user['username']}: {user['role']} (added {user.get('added_at', 'unknown')})")
        else:
            console.print("No users configured")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@rbac_app.command("audit-log")
def show_audit_log(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of entries to show"),
):
    """Show RBAC audit log."""
    try:
        log_entries = rbac_manager.get_audit_log(limit)
        if log_entries:
            console.print("[bold]📋 RBAC Audit Log[/bold]")
            for entry in log_entries[-limit:]:  # Show most recent first
                timestamp = entry['timestamp'][:19]  # Truncate ISO format
                console.print(f"  {timestamp} | {entry['performed_by']} | {entry['action']}")
                if entry.get('details'):
                    details = ', '.join(f"{k}={v}" for k, v in entry['details'].items())
                    console.print(f"    └─ {details}")
        else:
            console.print("No audit log entries")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Extended sync commands for additional cloud providers
@sync_app.command("push-k8s-secret")
def sync_push_k8s_secret(
    secret_name: str = typer.Argument(..., help="Kubernetes secret name"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="Kubernetes namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to push"),
):
    """Push profile to Kubernetes Secret."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("k8s_secret", namespace=namespace)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pushing profile '{profile}' to Kubernetes secret...", total=None)
            success = sync_service.push(profile, secret_name)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pushed profile '{profile}' to Kubernetes secret '{secret_name}'")
        else:
            console.print(f"[red]✗[/red] Failed to push profile '{profile}' to Kubernetes secret")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("pull-k8s-secret")
def sync_pull_k8s_secret(
    secret_name: str = typer.Argument(..., help="Kubernetes secret name"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="Kubernetes namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to pull into"),
):
    """Pull from Kubernetes Secret to profile."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("k8s_secret", namespace=namespace)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pulling from Kubernetes secret to profile '{profile}'...", total=None)
            success = sync_service.pull(profile, secret_name)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pulled into profile '{profile}' from Kubernetes secret")
        else:
            console.print(f"[red]✗[/red] Failed to pull from Kubernetes secret")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("push-k8s-configmap")
def sync_push_k8s_configmap(
    configmap_name: str = typer.Argument(..., help="Kubernetes ConfigMap name"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="Kubernetes namespace"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to push"),
):
    """Push profile to Kubernetes ConfigMap (non-sensitive vars only)."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("k8s_configmap", namespace=namespace)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pushing profile '{profile}' to Kubernetes ConfigMap...", total=None)
            success = sync_service.push(profile, configmap_name)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pushed profile '{profile}' to Kubernetes ConfigMap '{configmap_name}'")
        else:
            console.print(f"[red]✗[/red] Failed to push profile '{profile}' to Kubernetes ConfigMap")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("push-azure-kv")
def sync_push_azure_kv(
    prefix: str = typer.Option("", "--prefix", "-p", help="Secret name prefix"),
    profile: str = typer.Option(None, "--profile", help="Profile to push"),
):
    """Push profile to Azure Key Vault."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("azure_kv")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pushing profile '{profile}' to Azure Key Vault...", total=None)
            success = sync_service.push(profile, prefix)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pushed profile '{profile}' to Azure Key Vault")
        else:
            console.print(f"[red]✗[/red] Failed to push profile '{profile}' to Azure Key Vault")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("pull-azure-kv")
def sync_pull_azure_kv(
    prefix: str = typer.Option("", "--prefix", "-p", help="Secret name prefix"),
    profile: str = typer.Option(None, "--profile", help="Profile to pull into"),
):
    """Pull from Azure Key Vault to profile."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("azure_kv")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pulling from Azure Key Vault to profile '{profile}'...", total=None)
            success = sync_service.pull(profile, prefix)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pulled into profile '{profile}' from Azure Key Vault")
        else:
            console.print(f"[red]✗[/red] Failed to pull from Azure Key Vault")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("push-gcp-sm")
def sync_push_gcp_sm(
    prefix: str = typer.Option("", "--prefix", "-p", help="Secret name prefix"),
    profile: str = typer.Option(None, "--profile", help="Profile to push"),
):
    """Push profile to GCP Secret Manager."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("gcp_sm")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pushing profile '{profile}' to GCP Secret Manager...", total=None)
            success = sync_service.push(profile, prefix)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pushed profile '{profile}' to GCP Secret Manager")
        else:
            console.print(f"[red]✗[/red] Failed to push profile '{profile}' to GCP Secret Manager")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sync_app.command("pull-gcp-sm")
def sync_pull_gcp_sm(
    prefix: str = typer.Option("", "--prefix", "-p", help="Secret name prefix"),
    profile: str = typer.Option(None, "--profile", help="Profile to pull into"),
):
    """Pull from GCP Secret Manager to profile."""
    profile = profile or get_current_profile()
    try:
        sync_service = get_sync_service("gcp_sm")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Pulling from GCP Secret Manager to profile '{profile}'...", total=None)
            success = sync_service.pull(profile, prefix)
            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Successfully pulled into profile '{profile}' from GCP Secret Manager")
        else:
            console.print(f"[red]✗[/red] Failed to pull from GCP Secret Manager")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

# Monitoring commands
monitoring_app = typer.Typer()
app.add_typer(monitoring_app, name="monitor", help="Monitoring and alerting")

@monitoring_app.command("enable")
def enable_monitoring():
    """Enable monitoring and alerting."""
    try:
        monitor = MonitoringSystem()
        monitor.enable_monitoring()
        console.print("[green]✓[/green] Monitoring enabled")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@monitoring_app.command("disable")
def disable_monitoring():
    """Disable monitoring and alerting."""
    try:
        monitor = MonitoringSystem()
        monitor.disable_monitoring()
        console.print("[green]✓[/green] Monitoring disabled")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@monitoring_app.command("check")
def run_health_check():
    """Run health check and trigger alerts if needed."""
    try:
        monitor = MonitoringSystem()
        results = monitor.run_health_check()

        console.print("[bold]🔍 Health Check Results[/bold]")
        console.print(f"Status: {results.get('status', 'unknown')}")

        if 'checks' in results:
            for check_name, check_data in results['checks'].items():
                status_emoji = "✅" if check_data['status'] == 'healthy' else "⚠️"
                console.print(f"  {status_emoji} {check_name}: {check_data}")

        if results.get('alerts_triggered'):
            console.print(f"\n🚨 {len(results['alerts_triggered'])} alerts triggered")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@monitoring_app.command("status")
def monitoring_status():
    """Show monitoring status."""
    try:
        monitor = MonitoringSystem()
        status = monitor.get_health_status()

        console.print("[bold]📊 Monitoring Status[/bold]")
        for key, value in status.items():
            console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@monitoring_app.command("alerts")
def list_alerts(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of alerts to show"),
):
    """List recent alerts."""
    try:
        monitor = MonitoringSystem()
        alerts = monitor.list_alerts(limit)

        if alerts:
            console.print("[bold]🚨 Recent Alerts[/bold]")
            for alert in alerts:
                timestamp = alert['timestamp'][:19]
                emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(alert.get('severity'), "•")
                console.print(f"  {emoji} {timestamp} | {alert['type']} | {alert['message']}")
        else:
            console.print("No alerts found")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@monitoring_app.command("add-webhook")
def add_monitoring_webhook(
    url: str = typer.Argument(..., help="Webhook URL"),
):
    """Add webhook for monitoring alerts."""
    try:
        monitor = MonitoringSystem()
        monitor.add_alert_channel("webhook", {"url": url})
        console.print(f"[green]✓[/green] Monitoring webhook added: {url}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# CI/CD integration commands
ci_app = typer.Typer()
app.add_typer(ci_app, name="ci", help="CI/CD integration")

@ci_app.command("detect")
def detect_pipeline():
    """Detect the current CI/CD pipeline."""
    try:
        pipeline = CICDPipeline()
        info = pipeline.validate_pipeline_setup()

        console.print(f"[bold]🔧 CI/CD Detection[/bold]")
        console.print(f"Pipeline: {info['pipeline_type']}")
        console.print(f"Detected: {'Yes' if info['detected'] else 'No'}")

        if info['capabilities']:
            console.print("Capabilities:")
            for cap in info['capabilities']:
                console.print(f"  • {cap}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ci_app.command("load-secrets")
def load_ci_secrets(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to load secrets into"),
):
    """Load secrets from CI/CD pipeline."""
    profile = profile or get_current_profile()
    try:
        pipeline = CICDPipeline()
        success = pipeline.load_pipeline_secrets(profile)

        if success:
            console.print(f"[green]✓[/green] Loaded secrets into profile '{profile}'")
        else:
            console.print(f"[yellow]⚠️[/yellow] No secrets found or loaded into profile '{profile}'")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ci_app.command("generate-config")
def generate_ci_config(
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to generate config for"),
    pipeline: str = typer.Option(None, "--pipeline", help="Pipeline type"),
):
    """Generate CI/CD pipeline configuration."""
    profile = profile or get_current_profile()
    try:
        ci = CICDPipeline()
        config = ci.generate_pipeline_config(profile, pipeline)

        console.print(f"[bold]🔧 Generated {pipeline or ci.pipeline_type} Configuration[/bold]")
        console.print("=" * 50)
        console.print(config)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ci_app.command("promote")
def promote_environment(
    from_stage: str = typer.Argument(..., help="Source stage (dev, staging)"),
    to_stage: str = typer.Argument(..., help="Target stage (staging, prod)"),
):
    """Promote environment variables between stages."""
    try:
        promotion = EnvironmentPromotion()
        success = promotion.promote_environment(from_stage, to_stage)

        if success:
            console.print(f"[green]✓[/green] Successfully promoted from {from_stage} to {to_stage}")
        else:
            console.print(f"[red]✗[/red] Failed to promote from {from_stage} to {to_stage}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@ci_app.command("preview-promotion")
def preview_promotion(
    from_stage: str = typer.Argument(..., help="Source stage"),
    to_stage: str = typer.Argument(..., help="Target stage"),
):
    """Preview environment promotion changes."""
    try:
        promotion = EnvironmentPromotion()
        preview = promotion.preview_promotion(from_stage, to_stage)

        console.print(f"[bold]🔄 Promotion Preview: {from_stage} → {to_stage}[/bold]")
        console.print(f"Total changes: {preview['total_changes']}")

        for change_type, changes in preview['changes'].items():
            if changes:
                console.print(f"\n[bold]{change_type.title()}:[/bold]")
                for key, value in changes.items():
                    if isinstance(value, dict):
                        console.print(f"  {key}: {value['from']} → {value['to']}")
                    else:
                        console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# API Server command
@app.command("api-server")
def run_api_server(
    host: str = typer.Option("127.0.0.1", "--host", help="API server host"),
    port: int = typer.Option(8000, "--port", "-p", help="API server port"),
):
    """Start the EnvCLI REST API server."""
    try:
        console.print(f"[green]Starting EnvCLI API server on {host}:{port}[/green]")
        console.print(f"[dim]API documentation available at: http://{host}:{port}/docs[/dim]")
        start_api_server(host, port)
    except Exception as e:
        console.print(f"[red]Error starting API server:[/red] {e}")
        raise typer.Exit(1)

# Web Dashboard command
@app.command("web-dashboard")
def run_web_dashboard_cmd(
    port: int = typer.Option(8501, "--port", "-p", help="Web dashboard port"),
):
    """Launch the EnvCLI web dashboard."""
    try:
        from .web_dashboard import run_web_dashboard
        run_web_dashboard(port)
    except Exception as e:
        console.print(f"[red]Error starting web dashboard:[/red] {e}")
    raise typer.Exit(1)

# Predictive Analytics commands
predictive_app = typer.Typer()
app.add_typer(predictive_app, name="predict", help="Predictive analytics and forecasting")

@predictive_app.command("analyze")
def predictive_analyze():
    """Run predictive analysis on environment variables."""
    try:
        predictor = PredictiveAnalytics()
        results = predictor.analyze_variable_patterns()

        console.print(f"[bold]🔮 Predictive Analysis Results[/bold]")
        console.print(f"Total predictions: {results['total_predictions']}")

        if results["predictions"]:
            for prediction in results["predictions"][:10]:  # Show first 10
                emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "critical": "🚨"}.get(prediction.get("severity"), "•")
                console.print(f"  {emoji} [{prediction.get('profile', 'global')}] {prediction['prediction']}")
                if prediction.get("confidence"):
                    console.print(f"    Confidence: {prediction['confidence']:.1%}")
        else:
            console.print("✅ No predictions available")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@predictive_app.command("forecast")
def forecast_usage(
    days: int = typer.Option(30, "--days", "-d", help="Days to forecast"),
):
    """Forecast future usage trends."""
    try:
        predictor = PredictiveAnalytics()
        forecast = predictor.forecast_usage_trends(days)

        console.print(f"[bold]📈 Usage Forecast ({days} days)[/bold]")
        console.print(f"Current daily usage: {forecast.get('avg_daily', 0):.1f} commands")
        console.print(f"Forecasted daily usage: {forecast.get('forecasted_daily', 0):.1f} commands")
        console.print(f"Total forecasted: {forecast.get('forecasted_total', 0):.0f} commands")

        if forecast.get("predictions"):
            console.print("\n[bold]Forecast Insights:[/bold]")
            for pred in forecast["predictions"]:
                console.print(f"  • {pred['message']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@predictive_app.command("risk-assessment")
def risk_assessment():
    """Generate comprehensive risk assessment."""
    try:
        predictor = PredictiveAnalytics()
        assessment = predictor.get_risk_assessment()

        console.print(f"[bold]⚠️ Risk Assessment: {assessment['overall_risk'].upper()}[/bold]")

        if assessment["risk_factors"]:
            console.print("\n[bold]Risk Factors:[/bold]")
            for factor in assessment["risk_factors"]:
                console.print(f"  • {factor}")

        if assessment["recommendations"]:
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in assessment["recommendations"]:
                console.print(f"  • {rec}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

# Compliance Frameworks commands
compliance_app = typer.Typer()
app.add_typer(compliance_app, name="compliance", help="Compliance framework management")

@compliance_app.command("list")
def list_compliance_frameworks():
    """List available compliance frameworks."""
    try:
        manager = ComplianceFrameworkManager()
        frameworks = manager.list_frameworks()

        console.print("[bold]📋 Compliance Frameworks[/bold]")
        for name, info in frameworks.items():
            status = "✅ Enabled" if info["enabled"] else "❌ Disabled"
            console.print(f"  {name.upper()}: {info['name']} - {info['description']} [{status}]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@compliance_app.command("enable")
def enable_compliance_framework(
    framework: str = typer.Argument(..., help="Framework to enable: soc2, gdpr, hipaa"),
):
    """Enable a compliance framework."""
    try:
        manager = ComplianceFrameworkManager()
        manager.enable_framework(framework.lower())
        console.print(f"[green]✓[/green] Enabled compliance framework: {framework.upper()}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@compliance_app.command("disable")
def disable_compliance_framework(
    framework: str = typer.Argument(..., help="Framework to disable"),
):
    """Disable a compliance framework."""
    try:
        manager = ComplianceFrameworkManager()
        manager.disable_framework(framework.lower())
        console.print(f"[green]✓[/green] Disabled compliance framework: {framework.upper()}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@compliance_app.command("assess")
def assess_compliance(
    framework: str = typer.Argument(..., help="Framework to assess"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile to assess"),
):
    """Assess compliance for a profile."""
    profile = profile or get_current_profile()
    try:
        manager = ComplianceFrameworkManager()
        assessment = manager.assess_compliance(framework.lower(), profile)

        if "error" in assessment:
            console.print(f"[red]Error:[/red] {assessment['error']}")
            raise typer.Exit(1)

        console.print(f"[bold]📋 {framework.upper()} Compliance Assessment for '{profile}'[/bold]")
        console.print(f"Overall Status: {assessment['overall_compliance'].replace('_', ' ').title()}")

        if assessment.get("requirements_check"):
            console.print("\n[bold]Requirements Check:[/bold]")
            for req, check in assessment["requirements_check"].items():
                status = "✅" if check.get("compliant") else "❌"
                console.print(f"  {status} {req}: {check.get('details', 'Unknown')}")

        if assessment.get("recommendations"):
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in assessment["recommendations"]:
                console.print(f"  • {rec}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@compliance_app.command("report")
def generate_compliance_report(
    framework: str = typer.Argument(..., help="Framework for report"),
):
    """Generate comprehensive compliance report."""
    try:
        from .config import list_profiles
        profiles = list_profiles()

        manager = ComplianceFrameworkManager()
        report = manager.generate_compliance_report(framework.lower(), profiles)

        console.print(f"[bold]📊 {framework.upper()} Compliance Report[/bold]")
        console.print(f"Profiles assessed: {report['summary']['total_profiles']}")
        console.print(f"Compliant profiles: {report['summary']['compliant_profiles']}")
        console.print(f"Compliance rate: {report['summary']['compliance_rate']:.1%}")

        for profile, assessment in report["assessments"].items():
            status = assessment.get("overall_compliance", "unknown").replace("_", " ").title()
            console.print(f"  {profile}: {status}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
