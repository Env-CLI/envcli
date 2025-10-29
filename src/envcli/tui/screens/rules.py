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

