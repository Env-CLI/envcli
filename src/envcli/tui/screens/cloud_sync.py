"""
Cloud Sync screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, Input, Select
from textual.message import Message
from rich.text import Text
from rich.table import Table as RichTable

from ...sync import get_sync_service
from ...config import get_current_profile


class SyncConfigurator(Container):
    """Sync configuration dialog."""
    
    class SyncConfigured(Message):
        """Message sent when sync is configured."""
        def __init__(self, provider: str, config: dict, operation: str):
            self.provider = provider
            self.config = config
            self.operation = operation
            super().__init__()
    
    class ConfiguratorClosed(Message):
        """Message sent when configurator is closed."""
        pass
    
    def __init__(self, provider: str, operation: str = "push"):
        super().__init__()
        self.provider = provider
        self.operation = operation  # "push" or "pull"
        self.config_operation = operation  # Store for later use
    
    def compose(self) -> ComposeResult:
        """Compose the configurator."""
        title = f"{self.operation.title()} to {self.provider.upper()}"
        yield Static(title, classes="config-title")
        
        # Provider-specific configuration
        if self.provider == "aws_ssm":
            yield Label("AWS SSM Parameter Store Path:")
            yield Input(placeholder="/envcli/production", id="aws-path-input")
            
            info = Text()
            info.append("vFO ", style="#2196F3")
            info.append("Credentials from AWS CLI or environment variables", style="#757575")
            yield Static(info, classes="config-info")
            
        elif self.provider == "azure_kv":
            yield Label("Azure Key Vault URL:")
            yield Input(placeholder="https://myvault.vault.azure.net", id="azure-url-input")
            
            yield Label("Secret Prefix (optional):")
            yield Input(placeholder="envcli-", id="azure-prefix-input")
            
            info = Text()
            info.append("vFO ", style="#2196F3")
            info.append("Uses Azure DefaultAzureCredential", style="#757575")
            yield Static(info, classes="config-info")
            
        elif self.provider == "gcp_sm":
            yield Label("GCP Project ID:")
            yield Input(placeholder="my-project-id", id="gcp-project-input")
            
            yield Label("Secret Prefix (optional):")
            yield Input(placeholder="envcli-", id="gcp-prefix-input")
            
            info = Text()
            info.append("vFO ", style="#2196F3")
            info.append("Uses Application Default Credentials", style="#757575")
            yield Static(info, classes="config-info")
            
        elif self.provider == "vault":
            yield Label("Vault Address:")
            yield Input(placeholder="http://localhost:8200", id="vault-addr-input")
            
            yield Label("Vault Token:")
            yield Input(placeholder="s.xxxxxxxxxxxxx", id="vault-token-input", password=True)
            
            yield Label("Secret Path:")
            yield Input(placeholder="secret/envcli", id="vault-path-input")
            
            yield Label("Mount Point (optional):")
            yield Input(placeholder="secret", id="vault-mount-input")
            
        elif self.provider == "github":
            yield Label("GitHub Repository (owner/repo):")
            yield Input(placeholder="myorg/myrepo", id="github-repo-input")
            
            yield Label("GitHub Token:")
            yield Input(placeholder="ghp_xxxxxxxxxxxxx", id="github-token-input", password=True)
            
            info = Text()
            info.append("!️ ", style="#FFB300")
            info.append("GitHub Secrets are write-only (push only)", style="#FFB300")
            yield Static(info, classes="config-info")
            
        elif self.provider == "k8s":
            yield Label("Kubernetes Secret Name:")
            yield Input(placeholder="envcli-secrets", id="k8s-name-input")
            
            yield Label("Namespace:")
            yield Input(placeholder="default", id="k8s-namespace-input")
            
            info = Text()
            info.append("vFO ", style="#2196F3")
            info.append("Uses current kubectl context", style="#757575")
            yield Static(info, classes="config-info")
        
        # Action buttons
        with Horizontal(classes="config-actions"):
            yield Button("Confirm", variant="success", id="confirm-config-btn")
            yield Button("Cancel", variant="default", id="cancel-config-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "confirm-config-btn":
            config = self._gather_config()
            if config:
                self.post_message(self.SyncConfigured(self.provider, config, self.config_operation))
            else:
                self.app.notify("Please fill in all required fields", severity="error")
        elif button_id == "cancel-config-btn":
            self.post_message(self.ConfiguratorClosed())
    
    def _gather_config(self) -> dict:
        """Gather configuration from inputs."""
        config = {}
        
        try:
            if self.provider == "aws_ssm":
                path_input = self.query_one("#aws-path-input", Input)
                if not path_input.value.strip():
                    return None
                config["path"] = path_input.value.strip()
                
            elif self.provider == "azure_kv":
                url_input = self.query_one("#azure-url-input", Input)
                if not url_input.value.strip():
                    return None
                config["vault_url"] = url_input.value.strip()
                
                prefix_input = self.query_one("#azure-prefix-input", Input)
                config["prefix"] = prefix_input.value.strip()
                
            elif self.provider == "gcp_sm":
                project_input = self.query_one("#gcp-project-input", Input)
                if not project_input.value.strip():
                    return None
                config["project_id"] = project_input.value.strip()
                
                prefix_input = self.query_one("#gcp-prefix-input", Input)
                config["prefix"] = prefix_input.value.strip()
                
            elif self.provider == "vault":
                addr_input = self.query_one("#vault-addr-input", Input)
                token_input = self.query_one("#vault-token-input", Input)
                path_input = self.query_one("#vault-path-input", Input)
                
                if not all([addr_input.value.strip(), token_input.value.strip(), path_input.value.strip()]):
                    return None
                
                config["url"] = addr_input.value.strip()
                config["token"] = token_input.value.strip()
                config["path"] = path_input.value.strip()
                
                mount_input = self.query_one("#vault-mount-input", Input)
                config["mount_point"] = mount_input.value.strip() or "secret"
                
            elif self.provider == "github":
                repo_input = self.query_one("#github-repo-input", Input)
                token_input = self.query_one("#github-token-input", Input)
                
                if not all([repo_input.value.strip(), token_input.value.strip()]):
                    return None
                
                config["repo"] = repo_input.value.strip()
                config["token"] = token_input.value.strip()
                config["path"] = ""  # GitHub doesn't use path
                
            elif self.provider == "k8s":
                name_input = self.query_one("#k8s-name-input", Input)
                namespace_input = self.query_one("#k8s-namespace-input", Input)
                
                if not name_input.value.strip():
                    return None
                
                config["secret_name"] = name_input.value.strip()
                config["namespace"] = namespace_input.value.strip() or "default"
                config["path"] = config["secret_name"]  # Use secret name as path
            
            return config
        except Exception as e:
            self.app.log(f"Error gathering config: {e}")
            return None


class CloudSyncScreen(Container):
    """Main cloud sync screen."""
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
    
    def compose(self) -> ComposeResult:
        """Compose the cloud sync screen."""
        # Header
        yield Static("~ Cloud Sync & Integration", classes="screen-title")
        
        # Status bar
        status_text = Text()
        status_text.append("/ Profile: ", style="#757575")
        status_text.append(self.current_profile, style="bold #00E676")
        yield Static(status_text, classes="stats-bar")
        
        # Provider selection
        with Horizontal(classes="provider-bar"):
            yield Button("~ AWS SSM", variant="primary", id="provider-aws-btn")
            yield Button("~ Azure KV", variant="primary", id="provider-azure-btn")
            yield Button("~ GCP SM", variant="primary", id="provider-gcp-btn")
            yield Button("🔐 Vault", variant="primary", id="provider-vault-btn")
            yield Button("🐙 GitHub", variant="primary", id="provider-github-btn")
            yield Button("H K8s", variant="primary", id="provider-k8s-btn")
        
        # Main content area
        with VerticalScroll(classes="content-area", id="sync-content"):
            yield from self._create_info_display()
    
    def _create_info_display(self):
        """Create the information display."""
        # Provider info
        info = Text()
        info.append("~ Supported Cloud Providers\n\n", style="bold #00E676")
        
        info.append("AWS Systems Manager Parameter Store\n", style="bold #64FFDA")
        info.append("  • Secure, encrypted parameter storage\n", style="#E0E0E0")
        info.append("  • Requires AWS credentials configured\n", style="#757575")
        info.append("  • Supports push and pull operations\n\n", style="#757575")
        
        info.append("Azure Key Vault\n", style="bold #64FFDA")
        info.append("  • Enterprise-grade secret management\n", style="#E0E0E0")
        info.append("  • Uses Azure DefaultAzureCredential\n", style="#757575")
        info.append("  • Supports push and pull operations\n\n", style="#757575")
        
        info.append("Google Cloud Secret Manager\n", style="bold #64FFDA")
        info.append("  • Scalable secret management service\n", style="#E0E0E0")
        info.append("  • Uses Application Default Credentials\n", style="#757575")
        info.append("  • Supports push and pull operations\n\n", style="#757575")
        
        info.append("HashiCorp Vault\n", style="bold #64FFDA")
        info.append("  • Industry-standard secret management\n", style="#E0E0E0")
        info.append("  • Requires Vault address and token\n", style="#757575")
        info.append("  • Supports push and pull operations\n\n", style="#757575")
        
        info.append("GitHub Secrets\n", style="bold #64FFDA")
        info.append("  • Repository and organization secrets\n", style="#E0E0E0")
        info.append("  • Write-only (push only, no pull)\n", style="#FFB300")
        info.append("  • Encrypted with libsodium\n\n", style="#757575")
        
        info.append("Kubernetes Secrets\n", style="bold #64FFDA")
        info.append("  • Native Kubernetes secret storage\n", style="#E0E0E0")
        info.append("  • Uses current kubectl context\n", style="#757575")
        info.append("  • Supports push and pull operations\n\n", style="#757575")
        
        yield Static(info, classes="provider-info-text")
        
        # Usage instructions
        instructions = Text()
        instructions.append("\n📝 How to Use\n\n", style="bold #00E676")
        instructions.append("1. Click a provider button above\n", style="#E0E0E0")
        instructions.append("2. Choose Push (upload) or Pull (download)\n", style="#E0E0E0")
        instructions.append("3. Enter provider-specific configuration\n", style="#E0E0E0")
        instructions.append("4. Confirm to start sync operation\n\n", style="#E0E0E0")
        
        instructions.append("!️ Important Notes\n", style="bold #FFB300")
        instructions.append("• Push will overwrite remote secrets\n", style="#FFB300")
        instructions.append("• Pull will overwrite local profile\n", style="#FFB300")
        instructions.append("• Always backup before syncing\n", style="#FFB300")
        
        yield Static(instructions, classes="sync-instructions")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "provider-aws-btn":
            self.show_provider_menu("aws_ssm")
        elif button_id == "provider-azure-btn":
            self.show_provider_menu("azure_kv")
        elif button_id == "provider-gcp-btn":
            self.show_provider_menu("gcp_sm")
        elif button_id == "provider-vault-btn":
            self.show_provider_menu("vault")
        elif button_id == "provider-github-btn":
            self.show_provider_menu("github")
        elif button_id == "provider-k8s-btn":
            self.show_provider_menu("k8s")
        elif button_id and button_id.startswith("push-"):
            provider = button_id.replace("push-", "")
            self.show_configurator(provider, "push")
        elif button_id and button_id.startswith("pull-"):
            provider = button_id.replace("pull-", "")
            self.show_configurator(provider, "pull")
        elif button_id and button_id.startswith("status-"):
            provider = button_id.replace("status-", "")
            self.run_worker(self.check_status(provider))
        elif button_id == "close-menu-btn":
            self.run_worker(self._remove_menu())

    def show_provider_menu(self, provider: str) -> None:
        """Show provider operation menu."""
        self.run_worker(self._mount_menu(provider))

    async def _mount_menu(self, provider: str) -> None:
        """Mount the provider menu overlay."""
        try:
            existing = self.query_one(ProviderMenu)
            await existing.remove()
        except:
            pass

        menu = ProviderMenu(provider)
        await self.mount(menu)
        menu.add_class("overlay")

    async def _remove_menu(self) -> None:
        """Remove the provider menu overlay."""
        try:
            menu = self.query_one(ProviderMenu)
            await menu.remove()
        except:
            pass

    def show_configurator(self, provider: str, operation: str) -> None:
        """Show sync configurator."""
        self.run_worker(self._remove_menu())
        self.run_worker(self._mount_configurator(provider, operation))

    async def _mount_configurator(self, provider: str, operation: str) -> None:
        """Mount the configurator overlay."""
        try:
            existing = self.query_one(SyncConfigurator)
            await existing.remove()
        except:
            pass

        configurator = SyncConfigurator(provider, operation)
        await self.mount(configurator)
        configurator.add_class("overlay")

    def on_sync_configurator_sync_configured(self, message: SyncConfigurator.SyncConfigured) -> None:
        """Handle sync configured message."""
        self.run_worker(self._remove_configurator())
        self.run_worker(self.perform_sync(message.provider, message.config, message.operation))

    def on_sync_configurator_configurator_closed(self, message: SyncConfigurator.ConfiguratorClosed) -> None:
        """Handle configurator closed message."""
        self.run_worker(self._remove_configurator())

    async def _remove_configurator(self) -> None:
        """Remove the configurator overlay."""
        try:
            configurator = self.query_one(SyncConfigurator)
            await configurator.remove()
        except:
            pass

    async def perform_sync(self, provider: str, config: dict, operation: str) -> None:
        """Perform sync operation."""
        try:
            self.app.notify(f"Starting {operation} to {provider.upper()}...", severity="information")

            # Get sync service
            if provider == "aws_ssm":
                service = get_sync_service("aws_ssm")
                path = config["path"]
            elif provider == "azure_kv":
                service = get_sync_service("azure_kv", vault_url=config["vault_url"])
                path = config.get("prefix", "")
            elif provider == "gcp_sm":
                service = get_sync_service("gcp_sm", project_id=config["project_id"])
                path = config.get("prefix", "")
            elif provider == "vault":
                service = get_sync_service("vault", url=config["url"], token=config["token"], mount_point=config.get("mount_point", "secret"))
                path = config["path"]
            elif provider == "github":
                service = get_sync_service("github_secrets", repo=config["repo"], token=config["token"])
                path = ""
            elif provider == "k8s":
                service = get_sync_service("k8s_secret", namespace=config["namespace"])
                path = config["secret_name"]
            else:
                self.app.notify(f"Unknown provider: {provider}", severity="error")
                return

            # Perform operation
            if operation == "push":
                success = service.push(self.current_profile, path)
                if success:
                    self.app.notify(f"+ Successfully pushed to {provider.upper()}", severity="information")
                else:
                    self.app.notify(f"X Failed to push to {provider.upper()}", severity="error")
            else:
                success = service.pull(self.current_profile, path)
                if success:
                    self.app.notify(f"+ Successfully pulled from {provider.upper()}", severity="information")
                else:
                    self.app.notify(f"X Failed to pull from {provider.upper()}", severity="error")

        except Exception as e:
            self.app.notify(f"Sync failed: {e}", severity="error")

    async def check_status(self, provider: str) -> None:
        """Check sync status for a provider."""
        self.app.notify(f"Checking {provider.upper()} status...", severity="information")
        # TODO: Implement status checking
        self.app.notify("Status check - Coming soon!", severity="information")


class ProviderMenu(Container):
    """Provider operation menu."""

    class MenuClosed(Message):
        """Message sent when menu is closed."""
        pass

    def __init__(self, provider: str):
        super().__init__()
        self.provider = provider

    def compose(self) -> ComposeResult:
        """Compose the menu."""
        provider_names = {
            "aws_ssm": "AWS Systems Manager",
            "azure_kv": "Azure Key Vault",
            "gcp_sm": "Google Cloud Secret Manager",
            "vault": "HashiCorp Vault",
            "github": "GitHub Secrets",
            "k8s": "Kubernetes Secrets"
        }

        title = provider_names.get(self.provider, self.provider.upper())
        yield Static(f"~ {title}", classes="menu-title")

        # Operation buttons
        with Vertical(classes="menu-operations"):
            yield Button("⬆️ Push (Upload to Cloud)", variant="success", id=f"push-{self.provider}")

            # GitHub doesn't support pull
            if self.provider != "github":
                yield Button("⬇️ Pull (Download from Cloud)", variant="primary", id=f"pull-{self.provider}")

            yield Button("= Check Status", variant="default", id=f"status-{self.provider}")

        # Close button
        with Horizontal(classes="menu-actions"):
            yield Button("Close", variant="default", id="close-menu-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses - let them bubble up."""
        pass

