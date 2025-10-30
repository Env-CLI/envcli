"""
Rules & Policies screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, Input, DataTable
from textual.message import Message
from rich.text import Text

from ...ai_actions import AIActionExecutor
from ...config import get_current_profile


class RuleCard(Container):
    """Card displaying a single rule."""
    
    def __init__(self, rule: dict, rule_type: str, index: int):
        super().__init__()
        self.rule = rule
        self.rule_type = rule_type
        self.index = index
    
    def compose(self) -> ComposeResult:
        """Compose the rule card."""
        # Rule type indicator
        type_colors = {
            "naming_rules": "#00E676",
            "prefix_rules": "#64FFDA",
            "transformation_rules": "#FFB300",
            "exclusions": "#FF5252"
        }
        color = type_colors.get(self.rule_type, "#64FFDA")
        
        # Title
        title = Text()
        rule_type_display = self.rule_type.replace("_", " ").title()
        title.append(f"[{rule_type_display}] ", style=f"bold {color}")
        title.append(self.rule.get("description", "No description"), style="bold #E0E0E0")
        yield Static(title, classes="rule-title")
        
        # Pattern
        pattern = Text()
        pattern.append("FvD Pattern: ", style="#757575")
        pattern.append(self.rule.get("pattern", "N/A"), style="#00E676")
        yield Static(pattern, classes="rule-detail")
        
        # Target/Prefix/Transformation
        if "target_format" in self.rule:
            target = Text()
            target.append("🎯 Target: ", style="#757575")
            target.append(self.rule["target_format"], style="#64FFDA")
            yield Static(target, classes="rule-detail")
        elif "prefix" in self.rule:
            prefix = Text()
            prefix.append("+ Prefix: ", style="#757575")
            prefix.append(self.rule["prefix"], style="#64FFDA")
            yield Static(prefix, classes="rule-detail")
        elif "transformation" in self.rule:
            transform = Text()
            transform.append("@ Transform: ", style="#757575")
            transform.append(self.rule["transformation"], style="#64FFDA")
            yield Static(transform, classes="rule-detail")
        
        # Created date
        if "created_at" in self.rule:
            created = Text()
            created.append("📅 Created: ", style="#757575")
            created.append(self.rule["created_at"][:10], style="#757575")
            yield Static(created, classes="rule-detail")
        
        # Action buttons
        with Horizontal(classes="rule-actions"):
            yield Button("Delete", variant="error", id=f"delete-rule-{self.rule_type}-{self.index}")


class RuleEditor(Container):
    """Form for creating a new rule."""
    
    class RuleCreated(Message):
        """Message sent when a rule is created."""
        def __init__(self, rule_type: str):
            self.rule_type = rule_type
            super().__init__()
    
    class EditorClosed(Message):
        """Message sent when editor is closed."""
        pass
    
    def __init__(self, rule_type: str):
        super().__init__()
        self.rule_type = rule_type
    
    def compose(self) -> ComposeResult:
        """Compose the rule editor."""
        title_text = self.rule_type.replace("_", " ").title()
        yield Static(f"Create {title_text}", classes="editor-title")
        
        # Pattern input (common to all)
        yield Label("Pattern (regex):")
        yield Input(placeholder="e.g., .*_key$", id="pattern-input")
        
        # Type-specific inputs
        if self.rule_type == "naming_rules":
            yield Label("Target Format:")
            yield Input(placeholder="e.g., uppercase, SCREAMvG_SNAKE_CASE", id="target-input")
        elif self.rule_type == "prefix_rules":
            yield Label("Prefix:")
            yield Input(placeholder="e.g., APP_", id="prefix-input")
        elif self.rule_type == "transformation_rules":
            yield Label("Transformation:")
            yield Input(placeholder="e.g., replace:old:new", id="transform-input")
        
        # Description (common to all)
        yield Label("Description:")
        yield Input(placeholder="Brief description of this rule", id="description-input")
        
        # Action buttons
        with Horizontal(classes="editor-actions"):
            yield Button("Create", variant="success", id="create-rule-btn")
            yield Button("Cancel", variant="default", id="cancel-rule-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-rule-btn":
            self.create_rule()
        elif event.button.id == "cancel-rule-btn":
            self.post_message(self.EditorClosed())
    
    def create_rule(self) -> None:
        """Create the rule."""
        try:
            # Get pattern and description
            pattern_input = self.query_one("#pattern-input", Input)
            description_input = self.query_one("#description-input", Input)
            
            pattern = pattern_input.value.strip()
            description = description_input.value.strip()
            
            if not pattern:
                self.app.notify("Pattern is required", severity="error")
                return
            
            # Get type-specific fields
            executor = AIActionExecutor(get_current_profile())
            
            if self.rule_type == "naming_rules":
                target_input = self.query_one("#target-input", Input)
                target = target_input.value.strip()
                if not target:
                    self.app.notify("Target format is required", severity="error")
                    return
                executor.add_naming_rule(pattern, target, description)
            
            elif self.rule_type == "prefix_rules":
                prefix_input = self.query_one("#prefix-input", Input)
                prefix = prefix_input.value.strip()
                if not prefix:
                    self.app.notify("Prefix is required", severity="error")
                    return
                executor.add_prefix_rule(pattern, prefix, description)
            
            elif self.rule_type == "transformation_rules":
                transform_input = self.query_one("#transform-input", Input)
                transform = transform_input.value.strip()
                if not transform:
                    self.app.notify("Transformation is required", severity="error")
                    return
                executor.add_transformation_rule(pattern, transform, description)
            
            elif self.rule_type == "exclusions":
                executor.add_exclusion(pattern, description)
            
            self.app.notify(f"+ Rule created", severity="information")
            self.post_message(self.RuleCreated(self.rule_type))
        
        except Exception as e:
            self.app.notify(f"Failed to create rule: {e}", severity="error")


class RulesScreen(Container):
    """Main rules & policies screen."""
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.executor = AIActionExecutor(self.current_profile)
        self.rules = self.executor.list_custom_rules()
    
    def compose(self) -> ComposeResult:
        """Compose the rules screen."""
        # Header
        yield Static("Rules & Policies", classes="screen-title")
        
        # Status bar
        status_text = Text()
        status_text.append("/ Profile: ", style="#757575")
        status_text.append(self.current_profile, style="bold #00E676")
        status_text.append("  |  Rules: ", style="#757575")
        total_rules = sum(len(rules) for rules in [
            self.rules.get("naming_rules", []),
            self.rules.get("prefix_rules", []),
            self.rules.get("transformation_rules", []),
            self.rules.get("exclusions", [])
        ])
        status_text.append(str(total_rules), style="bold #00E676")
        status_text.append("  |  Status: ", style="#757575")
        if self.rules.get("enabled", True):
            status_text.append("+ Enabled", style="bold #00E676")
        else:
            status_text.append("X Disabled", style="bold #FF5252")
        yield Static(status_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("+ Add Naming Rule", variant="success", id="add-naming-btn")
            yield Button("+ Add Prefix Rule", variant="success", id="add-prefix-btn")
            yield Button("+ Add Transform Rule", variant="success", id="add-transform-btn")
            yield Button("+ Add Exclusion", variant="success", id="add-exclusion-btn")
            yield Button("⚙️ Manage Policies", variant="primary", id="manage-policies-btn")
            yield Button("@ Refresh", variant="default", id="refresh-rules-btn")
        
        # Rules list
        with Vertical(classes="content-area"):
            with VerticalScroll(classes="rules-list", id="rules-container"):
                yield from self._create_rules_list()
    
    def _create_rules_list(self):
        """Create the list of rule cards."""
        has_rules = False
        
        # Naming rules
        naming_rules = self.rules.get("naming_rules", [])
        if naming_rules:
            has_rules = True
            yield Static("Naming Rules", classes="rules-section-title")
            for i, rule in enumerate(naming_rules):
                yield RuleCard(rule, "naming_rules", i)
        
        # Prefix rules
        prefix_rules = self.rules.get("prefix_rules", [])
        if prefix_rules:
            has_rules = True
            yield Static("Prefix Rules", classes="rules-section-title")
            for i, rule in enumerate(prefix_rules):
                yield RuleCard(rule, "prefix_rules", i)
        
        # Transformation rules
        transform_rules = self.rules.get("transformation_rules", [])
        if transform_rules:
            has_rules = True
            yield Static("Transformation Rules", classes="rules-section-title")
            for i, rule in enumerate(transform_rules):
                yield RuleCard(rule, "transformation_rules", i)
        
        # Exclusions
        exclusions = self.rules.get("exclusions", [])
        if exclusions:
            has_rules = True
            yield Static("Exclusions", classes="rules-section-title")
            for i, rule in enumerate(exclusions):
                yield RuleCard(rule, "exclusions", i)
        
        if not has_rules:
            yield Static("No rules defined. Click a button above to add your first rule.", classes="placeholder-text")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "add-naming-btn":
            self.show_rule_editor("naming_rules")
        elif button_id == "add-prefix-btn":
            self.show_rule_editor("prefix_rules")
        elif button_id == "add-transform-btn":
            self.show_rule_editor("transformation_rules")
        elif button_id == "add-exclusion-btn":
            self.show_rule_editor("exclusions")
        elif button_id == "manage-policies-btn":
            self.show_policy_manager()
        elif button_id == "refresh-rules-btn":
            self.run_worker(self.refresh_rules())
        elif button_id and button_id.startswith("delete-rule-"):
            parts = button_id.replace("delete-rule-", "").rsplit("-", 1)
            if len(parts) == 2:
                rule_type = parts[0]
                index = int(parts[1])
                self.delete_rule(rule_type, index)
    
    def show_rule_editor(self, rule_type: str) -> None:
        """Show the rule editor."""
        self.run_worker(self._mount_editor(rule_type))
    
    async def _mount_editor(self, rule_type: str) -> None:
        """Mount the rule editor overlay."""
        try:
            existing = self.query_one(RuleEditor)
            await existing.remove()
        except:
            pass
        
        editor = RuleEditor(rule_type)
        await self.mount(editor)
        editor.add_class("overlay")
    
    def on_rule_editor_rule_created(self, message: RuleEditor.RuleCreated) -> None:
        """Handle rule created message."""
        self.run_worker(self._remove_editor())
        self.run_worker(self.refresh_rules())
    
    def on_rule_editor_editor_closed(self, message: RuleEditor.EditorClosed) -> None:
        """Handle editor closed message."""
        self.run_worker(self._remove_editor())

    def on_policy_manager_manager_closed(self, message: 'PolicyManager.ManagerClosed') -> None:
        """Handle policy manager closed message."""
        self.run_worker(self._remove_policy_manager())
    
    async def _remove_editor(self) -> None:
        """Remove the rule editor overlay."""
        try:
            editor = self.query_one(RuleEditor)
            await editor.remove()
        except:
            pass
    
    async def refresh_rules(self) -> None:
        """Refresh the rules list."""
        try:
            # Reload rules
            self.executor = AIActionExecutor(self.current_profile)
            self.rules = self.executor.list_custom_rules()
            
            # Update container
            container = self.query_one("#rules-container", VerticalScroll)
            await container.remove_children()
            
            # Recreate list
            for widget in self._create_rules_list():
                await container.mount(widget)
            
            self.app.notify("+ Rules refreshed", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to refresh rules: {e}", severity="error")
    
    def show_policy_manager(self) -> None:
        """Show the policy management interface."""
        self.run_worker(self._mount_policy_manager())

    async def _mount_policy_manager(self) -> None:
        """Mount the policy manager modal."""
        try:
            # Check for existing policy manager using CSS class selector
            existing = self.query_one('.policy-manager-overlay')
            await existing.remove()
        except:
            pass

        manager = PolicyManager()
        await self.mount(manager)
        manager.add_class("overlay")
        # Add an ID to make it easier to identify later
        manager.add_class("policy-manager-overlay")

    async def _remove_policy_manager(self) -> None:
        """Remove the policy manager modal."""
        try:
            # Use CSS selector to find the policy manager by its class
            manager = self.query_one('.policy-manager-overlay')
            await manager.remove()
        except:
            pass

    def delete_rule(self, rule_type: str, index: int) -> None:
        """Delete a rule."""
        try:
            success = self.executor.remove_rule(rule_type, index)
            if success:
                self.app.notify(f"+ Rule deleted", severity="information")
                self.run_worker(self.refresh_rules())
            else:
                self.app.notify("Failed to delete rule", severity="error")
        except Exception as e:
            self.app.notify(f"Error deleting rule: {e}", severity="error")

class PolicyManager(Container):
    """Modal for managing AI policy settings."""

    DEFAULT_CSS = """
    PolicyManager {
        width: 90;
        height: auto;
        max-height: 40;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    PolicyManager.overlay {
        align: center middle;
        layer: overlay;
    }

    .manager-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .policy-section {
        margin-bottom: 2;
        border: solid $border;
        padding: 1;
    }

    .policy-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .policy-controls {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-bottom: 1;
    }

    .policy-description {
        color: $text;
        margin-bottom: 1;
    }

    .manager-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    .manager-actions Button {
        margin: 0 1;
    }
    """

    class ManagerClosed(Message):
        """Message sent when manager is closed."""
        pass

    def compose(self) -> ComposeResult:
        """Compose the policy manager."""
        yield Static("🛡️ AI Policy Management", classes="manager-title")

        # Rules Enable/Disable
        with Vertical(classes="policy-section"):
            yield Static("📋 Custom Rules", classes="policy-title")
            yield Static("Enable or disable custom AI rules for this profile", classes="policy-description")

            with Horizontal(classes="policy-controls"):
                yield Button("🔓 Enable Rules", variant="success", id="enable-rules-btn")
                yield Button("🔒 Disable Rules", variant="error", id="disable-rules-btn")
                yield Button("📊 Rules Status", variant="default", id="rules-status-btn")

        # AI Analysis Settings
        with Vertical(classes="policy-section"):
            yield Static("🤖 AI Analysis Settings", classes="policy-title")
            yield Static("Configure AI-powered variable analysis and recommendations", classes="policy-description")

            with Horizontal(classes="policy-controls"):
                yield Button("⚙️ Analysis Settings", variant="primary", id="analysis-settings-btn")
                yield Button("📈 Usage Stats", variant="default", id="usage-stats-btn")
                yield Button("🔄 Reset AI State", variant="warning", id="reset-ai-btn")

        # Policy Templates
        with Vertical(classes="policy-section"):
            yield Static("📝 Policy Templates", classes="policy-title")
            yield Static("Load pre-configured policy templates for common scenarios", classes="policy-description")

            with Horizontal(classes="policy-controls"):
                yield Button("🏢 Enterprise", variant="primary", id="enterprise-template-btn")
                yield Button("🛠️ Development", variant="default", id="dev-template-btn")
                yield Button("🔒 Security Focused", variant="success", id="security-template-btn")

        # Advanced Settings
        with Vertical(classes="policy-section"):
            yield Static("⚙️ Advanced Policy Options", classes="policy-title")
            yield Static("Advanced configuration for power users", classes="policy-description")

            with Horizontal(classes="policy-controls"):
                yield Button("📋 Export Policies", variant="default", id="export-policies-btn")
                yield Button("📥 Import Policies", variant="default", id="import-policies-btn")
                yield Button("🗑️ Clear All Rules", variant="error", id="clear-rules-btn")

        # Action buttons
        with Horizontal(classes="manager-actions"):
            yield Button("💾 Save Settings", variant="success", id="save-settings-btn")
            yield Button("❌ Close", variant="default", id="close-manager-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-manager-btn":
            self.post_message(self.ManagerClosed())
        elif button_id == "enable-rules-btn":
            self.enable_rules()
        elif button_id == "disable-rules-btn":
            self.disable_rules()
        elif button_id == "rules-status-btn":
            self.show_rules_status()
        elif button_id == "analysis-settings-btn":
            self.show_analysis_settings()
        elif button_id == "usage-stats-btn":
            self.show_usage_stats()
        elif button_id == "reset-ai-btn":
            self.reset_ai_state()
        elif button_id == "enterprise-template-btn":
            self.load_enterprise_template()
        elif button_id == "dev-template-btn":
            self.load_dev_template()
        elif button_id == "security-template-btn":
            self.load_security_template()
        elif button_id == "export-policies-btn":
            self.export_policies()
        elif button_id == "import-policies-btn":
            self.import_policies()
        elif button_id == "clear-rules-btn":
            self.clear_all_rules()
        elif button_id == "save-settings-btn":
            self.save_settings()

    def enable_rules(self) -> None:
        """Enable custom rules."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)
            success = executor.enable_rules()
            if success:
                self.app.notify("✅ Custom rules enabled", severity="success")
            else:
                self.app.notify("❌ Failed to enable rules", severity="error")
        except Exception as e:
            self.app.notify(f"❌ Error enabling rules: {e}", severity="error")

    def disable_rules(self) -> None:
        """Disable custom rules."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)
            success = executor.disable_rules()
            if success:
                self.app.notify("✅ Custom rules disabled", severity="success")
            else:
                self.app.notify("❌ Failed to disable rules", severity="error")
        except Exception as e:
            self.app.notify(f"❌ Error disabling rules: {e}", severity="error")

    def show_rules_status(self) -> None:
        """Show current rules status."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)
            rules = executor.list_custom_rules()

            total_rules = sum(len(rules.get(rule_type, [])) for rule_type in ['naming_rules', 'prefix_rules', 'transformation_rules', 'exclusions'])
            enabled = rules.get("enabled", True)

            status_msg = f"Rules: {'Enabled' if enabled else 'Disabled'}, Total: {total_rules}"
            self.app.notify(f"📊 {status_msg}", severity="information", timeout=6)
        except Exception as e:
            self.app.notify(f"❌ Error getting status: {e}", severity="error")

    def show_analysis_settings(self) -> None:
        """Show AI analysis settings."""
        self.app.notify("⚙️ Analysis settings - Coming soon!", severity="information")

    def show_usage_stats(self) -> None:
        """Show AI usage statistics."""
        self.app.notify("📈 AI usage stats - Coming soon!", severity="information")

    def reset_ai_state(self) -> None:
        """Reset AI state."""
        self.app.notify("🔄 Reset AI state - Coming soon!", severity="information")

    def load_enterprise_template(self) -> None:
        """Load enterprise policy template."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)

            # Add enterprise-standard naming rules
            executor.add_naming_rule(r".*", "SCREAMING_SNAKE_CASE", "Force uppercase snake_case for all variables")
            executor.add_naming_rule(r".*", "no_spaces", "Remove spaces from variable names")

            # Add enterprise prefixes
            executor.add_prefix_rule(r".*", "APP_", "Add APP_ prefix to all variables")

            self.app.notify("✅ Enterprise template loaded", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Failed to load template: {e}", severity="error")

    def load_dev_template(self) -> None:
        """Load development policy template."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)

            # Development-friendly rules
            executor.add_naming_rule(r".*", "snake_case", "Use snake_case for development")
            executor.add_prefix_rule(r".*", "DEV_", "Add DEV_ prefix for development environment")

            self.app.notify("✅ Development template loaded", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Failed to load template: {e}", severity="error")

    def load_security_template(self) -> None:
        """Load security-focused policy template."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)

            # Security-focused rules
            executor.add_naming_rule(r".*secret.*", "SCREAMING_SNAKE_CASE", "Force uppercase for secrets")
            executor.add_naming_rule(r".*key.*", "SCREAMING_SNAKE_CASE", "Force uppercase for keys")
            executor.add_naming_rule(r".*token.*", "SCREAMING_SNAKE_CASE", "Force uppercase for tokens")
            executor.add_exclusion(r".*password.*", "Exclude password variables from AI processing")

            self.app.notify("✅ Security template loaded", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Failed to load template: {e}", severity="error")

    def export_policies(self) -> None:
        """Export current policies."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)
            policies = executor.list_custom_rules()

            import json
            from pathlib import Path
            from datetime import datetime

            export_file = Path.home() / f"envcli_policies_{profile}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(policies, f, indent=2)

            self.app.notify(f"✅ Policies exported to {export_file.name}", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Export failed: {e}", severity="error")

    def import_policies(self) -> None:
        """Import policies from file."""
        self.app.notify("📥 Import policies - Coming soon!", severity="information")

    def clear_all_rules(self) -> None:
        """Clear all rules (dangerous operation)."""
        try:
            profile = get_current_profile()
            executor = AIActionExecutor(profile)

            # Get current rules count
            rules = executor.list_custom_rules()
            total_rules = sum(len(rules.get(rule_type, [])) for rule_type in ['naming_rules', 'prefix_rules', 'transformation_rules', 'exclusions'])

            if total_rules == 0:
                self.app.notify("No rules to clear", severity="information")
                return

            # Clear all rules
            for rule_type in ['naming_rules', 'prefix_rules', 'transformation_rules', 'exclusions']:
                rules_list = rules.get(rule_type, [])
                for i in range(len(rules_list) - 1, -1, -1):  # Remove from end to start
                    executor.remove_rule(rule_type, i)

            self.app.notify(f"🗑️ Cleared {total_rules} rules", severity="warning")
        except Exception as e:
            self.app.notify(f"❌ Failed to clear rules: {e}", severity="error")




