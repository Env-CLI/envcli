"""
Kubernetes integration screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, DataTable, Input, Select, Label
from textual.containers import Container
from textual.message import Message
from ...kubernetes_integration import KubernetesSecretSync, KubernetesConfigMapSync
from ...config import get_current_profile


class KubernetesScreen(Container):
    """Kubernetes integration screen."""
    
    DEFAULT_CSS = """
    KubernetesScreen {
        background: #0E141B;
        padding: 1 2;
    }
    
    .k8s-header {
        height: 3;
        padding: 1 2;
        background: #1A2332;
        color: #00E676;
        text-style: bold;
    }
    
    .k8s-section {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        background: #1A2332;
        border: solid #37474F;
    }
    
    .k8s-section-title {
        color: #64FFDA;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .k8s-info {
        height: auto;
        padding: 1;
        background: #263238;
        border: solid #37474F;
        margin: 1 0;
    }
    
    .k8s-table {
        height: 15;
        margin: 1 0;
    }
    
    .k8s-input {
        width: 30;
        margin: 0 1;
    }
    
    .k8s-btn {
        margin: 0 1;
    }
    
    .k8s-status-synced {
        color: #00E676;
    }
    
    .k8s-status-out-of-sync {
        color: #FFB300;
    }
    
    .k8s-status-error {
        color: #FF5252;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.profile = get_current_profile()
        self.namespace = "default"
        self.k8s_secret_sync = None
        self.k8s_configmap_sync = None
        self._init_k8s_clients()
    
    def _init_k8s_clients(self):
        """Initialize Kubernetes clients."""
        try:
            self.k8s_secret_sync = KubernetesSecretSync(namespace=self.namespace)
            self.k8s_configmap_sync = KubernetesConfigMapSync(namespace=self.namespace)
        except Exception as e:
            self.app.log(f"Failed to initialize K8s clients: {e}")
    
    def compose(self) -> ComposeResult:
        """Compose the Kubernetes screen."""
        yield Static("H Kubernetes Integration", classes="k8s-header")
        
        with VerticalScroll():
            # Connection info
            with Container(classes="k8s-section"):
                yield Static("O Connection Status", classes="k8s-section-title")
                yield Static(self._get_connection_info(), id="connection-info", classes="k8s-info")
            
            # Namespace selector
            with Container(classes="k8s-section"):
                yield Static("> Namespace", classes="k8s-section-title")
                with Horizontal():
                    yield Input(
                        value=self.namespace,
                        placeholder="Enter namespace",
                        id="namespace-input",
                        classes="k8s-input"
                    )
                    yield Button("Switch Namespace", id="switch-namespace-btn", classes="k8s-btn")
            
            # Secrets management
            with Container(classes="k8s-section"):
                yield Static("[ Secrets", classes="k8s-section-title")
                yield DataTable(id="secrets-table", classes="k8s-table")
                with Horizontal():
                    yield Input(
                        placeholder="Secret name",
                        id="secret-name-input",
                        classes="k8s-input"
                    )
                    yield Button("^ Push", id="push-secret-btn", classes="k8s-btn", variant="success")
                    yield Button("v Pull", id="pull-secret-btn", classes="k8s-btn", variant="primary")
                    yield Button("@ Refresh", id="refresh-secrets-btn", classes="k8s-btn")
            
            # ConfigMaps management
            with Container(classes="k8s-section"):
                yield Static("- ConfigMaps", classes="k8s-section-title")
                yield DataTable(id="configmaps-table", classes="k8s-table")
                with Horizontal():
                    yield Input(
                        placeholder="ConfigMap name",
                        id="configmap-name-input",
                        classes="k8s-input"
                    )
                    yield Button("^ Push", id="push-configmap-btn", classes="k8s-btn", variant="success")
                    yield Button("@ Refresh", id="refresh-configmaps-btn", classes="k8s-btn")
    
    def on_mount(self) -> None:
        """Initialize tables when mounted."""
        self._setup_secrets_table()
        self._setup_configmaps_table()
        self.run_worker(self._load_secrets())
        self.run_worker(self._load_configmaps())
    
    def _get_connection_info(self) -> str:
        """Get Kubernetes connection information."""
        if self.k8s_secret_sync:
            return f"+ Connected to Kubernetes\nNamespace: {self.namespace}\nProfile: {self.profile}"
        else:
            return "❌ Not connected to Kubernetes\nCheck your kubeconfig"
    
    def _setup_secrets_table(self):
        """Setup secrets table columns."""
        table = self.query_one("#secrets-table", DataTable)
        table.add_columns("Secret Name", "Keys", "Status", "Age")
        table.cursor_type = "row"
    
    def _setup_configmaps_table(self):
        """Setup configmaps table columns."""
        table = self.query_one("#configmaps-table", DataTable)
        table.add_columns("ConfigMap Name", "Keys", "Age")
        table.cursor_type = "row"
    
    async def _load_secrets(self):
        """Load secrets from Kubernetes."""
        if not self.k8s_secret_sync:
            return
        
        try:
            secrets = self.k8s_secret_sync.list_secrets()
            table = self.query_one("#secrets-table", DataTable)
            table.clear()
            
            for secret_name in secrets:
                # Get status for this secret
                status_info = self.k8s_secret_sync.status(self.profile, secret_name)
                
                if "error" in status_info:
                    status = "❌ Error"
                    keys_count = "?"
                elif status_info.get("sync_status") == "synced":
                    status = "+ Synced"
                    keys_count = status_info.get("remote_count", "?")
                elif status_info.get("sync_status") == "out_of_sync":
                    status = "!️ Out of Sync"
                    keys_count = status_info.get("remote_count", "?")
                else:
                    status = "❓ Unknown"
                    keys_count = "?"
                
                table.add_row(secret_name, keys_count, status, "N/A")
            
            self.app.notify(f"Loaded {len(secrets)} secrets", severity="information")
        except Exception as e:
            self.app.log(f"Failed to load secrets: {e}")
            self.app.notify(f"Failed to load secrets: {e}", severity="error")
    
    async def _load_configmaps(self):
        """Load configmaps from Kubernetes."""
        if not self.k8s_configmap_sync:
            return
        
        try:
            # Note: KubernetesConfigMapSync doesn't have list_configmaps method
            # We'll need to add it or use the v1 API directly
            table = self.query_one("#configmaps-table", DataTable)
            table.clear()
            
            # For now, show a placeholder
            table.add_row("No ConfigMaps loaded", "0", "N/A")
            
        except Exception as e:
            self.app.log(f"Failed to load configmaps: {e}")
            self.app.notify(f"Failed to load configmaps: {e}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "switch-namespace-btn":
            self.run_worker(self._switch_namespace())
        elif button_id == "push-secret-btn":
            self.run_worker(self._push_secret())
        elif button_id == "pull-secret-btn":
            self.run_worker(self._pull_secret())
        elif button_id == "refresh-secrets-btn":
            self.run_worker(self._load_secrets())
        elif button_id == "push-configmap-btn":
            self.run_worker(self._push_configmap())
        elif button_id == "refresh-configmaps-btn":
            self.run_worker(self._load_configmaps())
    
    async def _switch_namespace(self):
        """Switch to a different namespace."""
        namespace_input = self.query_one("#namespace-input", Input)
        new_namespace = namespace_input.value.strip()
        
        if not new_namespace:
            self.app.notify("Please enter a namespace", severity="warning")
            return
        
        self.namespace = new_namespace
        self._init_k8s_clients()
        
        # Update connection info
        connection_info = self.query_one("#connection-info", Static)
        connection_info.update(self._get_connection_info())
        
        # Reload data
        await self._load_secrets()
        await self._load_configmaps()
        
        self.app.notify(f"Switched to namespace: {new_namespace}", severity="success")
    
    async def _push_secret(self):
        """Push profile to Kubernetes secret."""
        secret_input = self.query_one("#secret-name-input", Input)
        secret_name = secret_input.value.strip()
        
        if not secret_name:
            self.app.notify("Please enter a secret name", severity="warning")
            return
        
        if not self.k8s_secret_sync:
            self.app.notify("Not connected to Kubernetes", severity="error")
            return
        
        try:
            success = self.k8s_secret_sync.push(self.profile, secret_name)
            if success:
                self.app.notify(f"+ Pushed to secret: {secret_name}", severity="success")
                await self._load_secrets()
            else:
                self.app.notify(f"Failed to push to secret: {secret_name}", severity="error")
        except Exception as e:
            self.app.log(f"Push secret error: {e}")
            self.app.notify(f"Error: {e}", severity="error")
    
    async def _pull_secret(self):
        """Pull from Kubernetes secret to profile."""
        secret_input = self.query_one("#secret-name-input", Input)
        secret_name = secret_input.value.strip()
        
        if not secret_name:
            self.app.notify("Please enter a secret name", severity="warning")
            return
        
        if not self.k8s_secret_sync:
            self.app.notify("Not connected to Kubernetes", severity="error")
            return
        
        try:
            success = self.k8s_secret_sync.pull(self.profile, secret_name)
            if success:
                self.app.notify(f"+ Pulled from secret: {secret_name}", severity="success")
            else:
                self.app.notify(f"Failed to pull from secret: {secret_name}", severity="error")
        except Exception as e:
            self.app.log(f"Pull secret error: {e}")
            self.app.notify(f"Error: {e}", severity="error")
    
    async def _push_configmap(self):
        """Push profile to Kubernetes ConfigMap."""
        configmap_input = self.query_one("#configmap-name-input", Input)
        configmap_name = configmap_input.value.strip()
        
        if not configmap_name:
            self.app.notify("Please enter a ConfigMap name", severity="warning")
            return
        
        if not self.k8s_configmap_sync:
            self.app.notify("Not connected to Kubernetes", severity="error")
            return
        
        try:
            success = self.k8s_configmap_sync.push(self.profile, configmap_name, exclude_secrets=True)
            if success:
                self.app.notify(f"+ Pushed to ConfigMap: {configmap_name}", severity="success")
                await self._load_configmaps()
            else:
                self.app.notify(f"Failed to push to ConfigMap: {configmap_name}", severity="error")
        except Exception as e:
            self.app.log(f"Push ConfigMap error: {e}")
            self.app.notify(f"Error: {e}", severity="error")

