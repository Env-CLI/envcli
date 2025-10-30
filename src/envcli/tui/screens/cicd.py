"""CI/CD integration screen for EnvCLI TUI."""

from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Select, DataTable, Label, Input
from textual.message import Message
from ...ci_cd_integration import CICDPipeline, EnvironmentPromotion
from ...config import get_current_profile, list_profiles
from ...env_manager import EnvManager


class CICDScreen(Container):
    """CI/CD integration management screen."""
    
    DEFAULT_CSS = """
    CICDScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }
    
    .status-box {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }
    
    .section {
        border: solid $accent;
        padding: 1;
        margin-top: 1;
        height: auto;
    }
    
    .button-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    
    .button-row Button {
        margin-right: 1;
    }
    
    DataTable {
        height: 15;
        margin-top: 1;
    }
    
    #config-display {
        border: solid $accent;
        padding: 1;
        margin-top: 1;
        height: 20;
        overflow-y: auto;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.pipeline = CICDPipeline()
        self.promotion = EnvironmentPromotion()
        self.current_profile = get_current_profile()
        self.selected_pipeline_type = None
    
    def compose(self):
        """Compose the CI/CD screen."""
        with VerticalScroll():
            yield Static("🚀 CI/CD Integration", classes="header")
            
            # Pipeline status
            yield Static(self._get_pipeline_status(), id="pipeline-status", classes="status-box")
            
            # Pipeline type selector
            with Horizontal(classes="button-row"):
                yield Label("Pipeline Type:")
                yield Select(
                    [
                        ("GitHub Actions", "github_actions"),
                        ("GitLab CI", "gitlab_ci"),
                        ("Jenkins", "jenkins"),
                        ("CircleCI", "circleci"),
                        ("Travis CI", "travis_ci"),
                        ("Auto-detect", "auto")
                    ],
                    value="auto",
                    id="pipeline-selector"
                )
                yield Button("🔍 Detect Pipeline", id="detect-btn", variant="primary")
                yield Button("🔄 Refresh", id="refresh-btn")
            
            # Pipeline actions
            with Horizontal(classes="button-row"):
                yield Button("📥 Load Secrets", id="load-secrets-btn", variant="success")
                yield Button("📄 Generate Config", id="generate-config-btn")
                yield Button("✅ Validate Setup", id="validate-btn")
            
            # Environment promotion section
            with Vertical(classes="section"):
                yield Static("🔄 Environment Promotion", classes="header")
                with Horizontal(classes="button-row"):
                    yield Label("From:")
                    yield Select(
                        [(p, p) for p in list_profiles()],
                        id="from-stage-selector"
                    )
                    yield Label("To:")
                    yield Select(
                        [(p, p) for p in list_profiles()],
                        id="to-stage-selector"
                    )
                    yield Button("👁️ Preview", id="preview-promotion-btn")
                    yield Button("🚀 Promote", id="promote-btn", variant="success")
            
            # Pipeline variables table
            yield Static("📦 Pipeline Variables", classes="header")
            yield DataTable(id="pipeline-vars-table")
            
            # Generated config display
            yield Static("📄 Generated Configuration", classes="header")
            yield Static("", id="config-display")
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        self._setup_pipeline_vars_table()
        self._load_pipeline_vars()
        self._update_pipeline_status()
    
    def _get_pipeline_status(self) -> str:
        """Get pipeline status summary."""
        validation = self.pipeline.validate_pipeline_setup()
        
        status = f"Pipeline Type: {validation['pipeline_type']}\n"
        status += f"Detected: {'✅ Yes' if validation['detected'] else '❌ No'}\n"
        
        if validation['capabilities']:
            status += f"Capabilities: {', '.join(validation['capabilities'])}\n"
        
        status += f"Current Profile: {self.current_profile}"
        
        return status
    
    def _setup_pipeline_vars_table(self) -> None:
        """Setup the pipeline variables table."""
        table = self.query_one("#pipeline-vars-table", DataTable)
        table.add_column("Variable", key="variable")
        table.add_column("Value", key="value")
        table.add_column("Source", key="source")
        table.cursor_type = "row"
    
    async def _load_pipeline_vars(self) -> None:
        """Load pipeline variables."""
        table = self.query_one("#pipeline-vars-table", DataTable)
        table.clear()
        
        # Load current profile variables
        manager = EnvManager(self.current_profile)
        env_vars = manager.load_env()
        
        for key, value in env_vars.items():
            # Mask sensitive values
            display_value = value
            if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                display_value = '*' * 8
            
            table.add_row(key, display_value, self.current_profile)
    
    async def _update_pipeline_status(self) -> None:
        """Update pipeline status display."""
        status_widget = self.query_one("#pipeline-status", Static)
        status_widget.update(self._get_pipeline_status())
    
    async def _detect_pipeline(self) -> None:
        """Detect the current CI/CD pipeline."""
        self.pipeline = CICDPipeline("auto")
        validation = self.pipeline.validate_pipeline_setup()
        
        # Update selector
        selector = self.query_one("#pipeline-selector", Select)
        selector.value = validation['pipeline_type']
        
        await self._update_pipeline_status()
        self.notify(f"Detected pipeline: {validation['pipeline_type']}")
    
    async def _load_secrets(self) -> None:
        """Load secrets from CI/CD pipeline."""
        # Check if we're actually in a CI/CD environment
        validation = self.pipeline.validate_pipeline_setup()

        if not validation['detected']:
            self.notify("⚠️ No CI/CD pipeline detected. This feature only works when running inside a CI/CD environment (GitHub Actions, GitLab CI, Jenkins, etc.)", severity="warning", timeout=10)
            return

        success = self.pipeline.load_pipeline_secrets(self.current_profile)

        if success:
            self.notify("✅ Secrets loaded successfully", severity="information")
            await self._load_pipeline_vars()
        else:
            self.notify("❌ Failed to load secrets. Make sure secrets are configured in your CI/CD pipeline.", severity="error", timeout=8)
    
    async def _generate_config(self) -> None:
        """Generate pipeline configuration."""
        selector = self.query_one("#pipeline-selector", Select)
        pipeline_type = selector.value
        
        config = self.pipeline.generate_pipeline_config(self.current_profile, pipeline_type)
        
        config_display = self.query_one("#config-display", Static)
        config_display.update(config)
        
        self.notify(f"Generated {pipeline_type} configuration")
    
    async def _validate_setup(self) -> None:
        """Validate pipeline setup."""
        validation = self.pipeline.validate_pipeline_setup()
        
        if validation['detected']:
            self.notify("✅ Pipeline setup is valid", severity="information")
        else:
            self.notify("⚠️ No pipeline detected", severity="warning")
        
        await self._update_pipeline_status()
    
    async def _preview_promotion(self) -> None:
        """Preview environment promotion."""
        from_selector = self.query_one("#from-stage-selector", Select)
        to_selector = self.query_one("#to-stage-selector", Select)
        
        from_stage = from_selector.value
        to_stage = to_selector.value
        
        if not from_stage or not to_stage:
            self.notify("⚠️ Please select both stages", severity="warning")
            return
        
        try:
            preview = self.promotion.preview_promotion(from_stage, to_stage)
            
            message = f"Promotion Preview: {from_stage} → {to_stage}\n"
            message += f"Total changes: {preview['total_changes']}\n"
            message += f"Added: {len(preview['changes']['added'])}\n"
            message += f"Modified: {len(preview['changes']['modified'])}\n"
            message += f"Removed: {len(preview['changes']['removed'])}"
            
            self.notify(message, severity="information", timeout=10)
        except Exception as e:
            self.notify(f"❌ Preview failed: {e}", severity="error")
    
    async def _promote_environment(self) -> None:
        """Promote environment variables."""
        from_selector = self.query_one("#from-stage-selector", Select)
        to_selector = self.query_one("#to-stage-selector", Select)
        
        from_stage = from_selector.value
        to_stage = to_selector.value
        
        if not from_stage or not to_stage:
            self.notify("⚠️ Please select both stages", severity="warning")
            return
        
        success = self.promotion.promote_environment(from_stage, to_stage)
        
        if success:
            self.notify(f"✅ Promoted {from_stage} → {to_stage}", severity="information")
            await self._load_pipeline_vars()
        else:
            self.notify("❌ Promotion failed", severity="error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "detect-btn":
            await self._detect_pipeline()
        elif button_id == "refresh-btn":
            await self._load_pipeline_vars()
            await self._update_pipeline_status()
        elif button_id == "load-secrets-btn":
            await self._load_secrets()
        elif button_id == "generate-config-btn":
            await self._generate_config()
        elif button_id == "validate-btn":
            await self._validate_setup()
        elif button_id == "preview-promotion-btn":
            await self._preview_promotion()
        elif button_id == "promote-btn":
            await self._promote_environment()
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "pipeline-selector":
            self.selected_pipeline_type = event.value
            self.pipeline.pipeline_type = event.value
            await self._update_pipeline_status()

