"""
AI Analysis screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, DataTable
from textual.message import Message
from rich.text import Text

from ...ai_assistant import AIAssistant
from ...ai_actions import AIActionExecutor
from ...config import get_current_profile


class RecommendationCard(Container):
    """Card displaying a single AI recommendation."""
    
    def __init__(self, recommendation: dict, index: int):
        super().__init__()
        self.recommendation = recommendation
        self.index = index
    
    def compose(self) -> ComposeResult:
        """Compose the recommendation card."""
        # Severity indicator
        severity = self.recommendation.get("severity", "info")
        severity_colors = {
            "error": "#FF5252",
            "warning": "#FFB300",
            "info": "#64FFDA"
        }
        color = severity_colors.get(severity, "#64FFDA")
        
        # Title
        title = Text()
        title.append(f"[{severity.upper()}] ", style=f"bold {color}")
        title.append(self.recommendation.get("message", "No message"), style="bold #E0E0E0")
        yield Static(title, classes="recommendation-title")
        
        # Details
        if "suggestion" in self.recommendation:
            suggestion = Text()
            suggestion.append("💡 Suggestion: ", style="#757575")
            suggestion.append(self.recommendation["suggestion"], style="#00E676")
            yield Static(suggestion, classes="recommendation-detail")
        
        if "variable" in self.recommendation:
            variable = Text()
            variable.append("📌 Variable: ", style="#757575")
            variable.append(self.recommendation["variable"], style="#64FFDA")
            yield Static(variable, classes="recommendation-detail")
        
        # Action button
        with Horizontal(classes="recommendation-actions"):
            yield Button("Apply", variant="success", id=f"apply-rec-{self.index}")
            yield Button("Dismiss", variant="default", id=f"dismiss-rec-{self.index}")


class ActionPreview(Container):
    """Preview of pending AI actions."""
    
    def __init__(self, actions: list):
        super().__init__()
        self.actions = actions
    
    def compose(self) -> ComposeResult:
        """Compose the action preview."""
        yield Static("Pending Actions", classes="preview-title")
        
        if not self.actions:
            yield Static("No pending actions", classes="preview-empty")
            return
        
        # Create table
        table = DataTable(id="actions-table")
        table.add_columns("Type", "Description", "Status")
        
        for action in self.actions:
            action_type = action.get("action_type", "unknown")
            description = action.get("description", "No description")
            status = "+ Applied" if action.get("applied", False) else "⏳ Pending"
            table.add_row(action_type, description, status)
        
        yield table
        
        # Action buttons
        with Horizontal(classes="preview-actions"):
            yield Button("Apply All", variant="success", id="apply-all-actions-btn")
            yield Button("Clear All", variant="error", id="clear-all-actions-btn")


class AIAnalysisScreen(Container):
    """Main AI analysis screen."""
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.assistant = AIAssistant()
        self.executor = AIActionExecutor(self.current_profile)
        self.recommendations = []
        self.show_preview = False
    
    def compose(self) -> ComposeResult:
        """Compose the AI analysis screen."""
        # Header
        yield Static("AI Analysis & Recommendations", classes="screen-title")
        
        # Status bar
        status_text = Text()
        status_text.append("* AI Provider: ", style="#757575")
        provider_name = self.assistant.config.get("provider", "none")
        status_text.append(provider_name, style="bold #00E676")
        status_text.append("  |  / Profile: ", style="#757575")
        status_text.append(self.current_profile, style="bold #00E676")
        status_text.append("  |  Status: ", style="#757575")
        if self.assistant.enabled:
            status_text.append("+ Enabled", style="bold #00E676")
        else:
            status_text.append("X Disabled", style="bold #FF5252")
        yield Static(status_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("FvD Run Analysis", variant="success", id="run-analysis-btn")
            yield Button("- View Actions", variant="primary", id="view-actions-btn")
            yield Button("# Custom Rules", variant="default", id="custom-rules-btn")
            yield Button("O History", variant="default", id="history-btn")
            yield Button("@ Refresh", variant="default", id="refresh-ai-btn")
        
        # Main content area
        with Vertical(classes="content-area"):
            if not self.assistant.enabled:
                # Show enable message
                enable_msg = Text()
                enable_msg.append("!️ AI features are disabled\n\n", style="bold #FFB300")
                enable_msg.append("To enable AI analysis, run:\n", style="#757575")
                enable_msg.append("  envcli ai enable\n\n", style="#00E676")
                enable_msg.append("Or configure a provider:\n", style="#757575")
                enable_msg.append("  envcli ai config --provider openai", style="#00E676")
                yield Static(enable_msg, classes="ai-disabled-message")
            else:
                # Recommendations list
                with VerticalScroll(classes="recommendations-list", id="recommendations-container"):
                    yield Static("Click 'Run Analysis' to get AI recommendations", classes="placeholder-text")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "run-analysis-btn":
            self.app.notify("Running AI analysis...", severity="information")
            self.run_worker(self.run_analysis())
        elif button_id == "view-actions-btn":
            self.show_actions_preview()
        elif button_id == "custom-rules-btn":
            self.app.notify("Custom Rules - Coming soon!", severity="information")
        elif button_id == "history-btn":
            self.show_action_history()
        elif button_id == "refresh-ai-btn":
            self.run_worker(self.refresh_recommendations())
        elif button_id == "apply-all-actions-btn":
            self.run_worker(self.apply_all_actions())
        elif button_id == "clear-all-actions-btn":
            self.clear_all_actions()
        elif button_id and button_id.startswith("apply-rec-"):
            index = int(button_id.replace("apply-rec-", ""))
            self.apply_recommendation(index)
        elif button_id and button_id.startswith("dismiss-rec-"):
            index = int(button_id.replace("dismiss-rec-", ""))
            self.dismiss_recommendation(index)
    
    async def run_analysis(self) -> None:
        """Run AI analysis on current profile."""
        try:
            # Generate recommendations
            result = self.assistant.generate_recommendations(self.current_profile)

            if "error" in result:
                self.app.notify(f"Error: {result['error']}", severity="error")
                return

            # Get pattern-based recommendations
            raw_recommendations = self.assistant.analyze_variable_naming(self.current_profile)

            # Filter out recommendations for variables that don't exist anymore
            from ...env_manager import EnvManager
            manager = EnvManager(self.current_profile)
            current_vars = manager.load_env()

            self.recommendations = []
            for rec in raw_recommendations:
                variable = rec.get("variable", "")
                if variable in current_vars:
                    self.recommendations.append(rec)
                else:
                    self.app.log(f"Skipping recommendation for non-existent variable: {variable}")

            # Update display
            await self.refresh_recommendations()

            skipped = len(raw_recommendations) - len(self.recommendations)
            if skipped > 0:
                self.app.notify(f"+ Found {len(self.recommendations)} recommendations ({skipped} already applied)", severity="information")
            else:
                self.app.notify(f"+ Found {len(self.recommendations)} recommendations", severity="information")
        except Exception as e:
            self.app.notify(f"Analysis failed: {e}", severity="error")
    
    async def refresh_recommendations(self) -> None:
        """Refresh the recommendations display."""
        try:
            container = self.query_one("#recommendations-container", VerticalScroll)
            
            # Clear existing content
            await container.remove_children()
            
            if not self.recommendations:
                await container.mount(Static("No recommendations found", classes="placeholder-text"))
            else:
                # Mount recommendation cards
                for i, rec in enumerate(self.recommendations):
                    await container.mount(RecommendationCard(rec, i))
        except Exception as e:
            self.app.log(f"Failed to refresh recommendations: {e}")
    
    def show_actions_preview(self) -> None:
        """Show preview of pending actions."""
        actions = self.executor.preview_actions()
        self.app.notify(f"Pending actions: {len(actions)}", severity="information")
        self.run_worker(self._mount_action_preview(actions))
    
    async def _mount_action_preview(self, actions: list) -> None:
        """Mount the action preview overlay."""
        try:
            existing = self.query_one(ActionPreview)
            await existing.remove()
        except:
            pass
        
        preview = ActionPreview(actions)
        await self.mount(preview)
        preview.add_class("overlay")
    
    async def apply_all_actions(self) -> None:
        """Apply all pending actions."""
        result = self.executor.apply_all_actions(dry_run=False)
        
        success = result["successful"]
        failed = result["failed"]
        
        if success > 0:
            self.app.notify(f"+ Applied {success} actions", severity="information")
        if failed > 0:
            self.app.notify(f"X {failed} actions failed", severity="error")
        
        # Refresh recommendations
        await self.run_analysis()
    
    def clear_all_actions(self) -> None:
        """Clear all pending actions."""
        self.executor.actions = []
        self.app.notify("Cleared all pending actions", severity="information")
    
    def apply_recommendation(self, index: int) -> None:
        """Apply a single recommendation."""
        if index < len(self.recommendations):
            rec = self.recommendations[index]
            self.app.notify(f"Applying recommendation: {rec.get('message', 'Unknown')}", severity="information")
            self.run_worker(self._apply_recommendation_async(rec, index))

    async def _apply_recommendation_async(self, rec: dict, index: int) -> None:
        """Apply a recommendation asynchronously."""
        try:
            from ...env_manager import EnvManager

            # Get the suggestion from the recommendation
            suggestion = rec.get("suggestion", "")
            variable = rec.get("variable", "")

            self.app.log(f"Applying recommendation - Variable: {variable}, Suggestion: {suggestion}")

            # Parse the suggestion to extract the new name
            # Common patterns:
            # - "Rename to: NEW_NAME"
            # - "Consider renaming to: NEW_NAME"
            # - "Rename to 'NEW_NAME'"
            new_name = None
            import re

            # Try to extract from quotes first
            match = re.search(r"['\"]([^'\"]+)['\"]", suggestion)
            if match:
                new_name = match.group(1)
                self.app.log(f"Extracted new name (with quotes): {new_name}")
            elif "rename" in suggestion.lower() or "renaming" in suggestion.lower():
                # Try without quotes - match after "to:" or "to "
                match = re.search(r"to[:\s]+([A-Z_][A-Z0-9_]*)", suggestion)
                if match:
                    new_name = match.group(1)
                    self.app.log(f"Extracted new name (without quotes): {new_name}")

            if not new_name or not variable:
                self.app.log(f"Failed to parse - new_name: {new_name}, variable: {variable}")
                self.app.notify("Could not parse recommendation", severity="error")
                return

            self.app.log(f"Applying rename: {variable} -> {new_name}")

            # Apply the rename
            manager = EnvManager(self.current_profile)
            env_vars = manager.load_env()

            self.app.log(f"Loaded {len(env_vars)} variables from profile")

            if variable not in env_vars:
                self.app.log(f"Variable '{variable}' not found in env_vars")
                self.app.notify(f"Variable '{variable}' not found (may have been already renamed)", severity="warning")
                # Remove this stale recommendation
                self.recommendations.pop(index)
                await self.refresh_recommendations()
                return

            if new_name in env_vars:
                self.app.log(f"Variable '{new_name}' already exists")
                self.app.notify(f"Variable '{new_name}' already exists", severity="error")
                return

            # Perform the rename
            value = env_vars[variable]
            self.app.log(f"Renaming: {variable} = {value[:20]}... -> {new_name}")
            del env_vars[variable]
            env_vars[new_name] = value
            manager.save_env(env_vars)

            self.app.log(f"Saved changes to profile")

            # Remove the recommendation
            self.recommendations.pop(index)
            await self.refresh_recommendations()

            self.app.notify(f"+ Renamed '{variable}' to '{new_name}'", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to apply recommendation: {e}", severity="error")
            self.app.log(f"Error applying recommendation: {e}")

    def dismiss_recommendation(self, index: int) -> None:
        """Dismiss a recommendation."""
        if index < len(self.recommendations):
            self.recommendations.pop(index)
            self.run_worker(self.refresh_recommendations())
            self.app.notify("Recommendation dismissed", severity="information")
    
    def show_action_history(self) -> None:
        """Show history of applied actions."""
        history = self.executor.get_action_history(limit=20)
        self.app.notify(f"Action history: {len(history)} entries", severity="information")
        # TODO: Show history in overlay

