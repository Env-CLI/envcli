"""Variables management screen for EnvCLI TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Input, Label
from textual.message import Message
from textual.screen import ModalScreen
from rich.text import Text
from typing import Dict, Optional
import json
from pathlib import Path

from ...env_manager import EnvManager
from ...config import get_current_profile


class VariableRow(Container):
    """A row displaying a single variable."""
    
    def __init__(self, key: str, value: str, masked: bool = True):
        super().__init__()
        self.key = key
        self.value = value
        self.masked = masked
        self.is_sensitive = any(word in key.lower() for word in ['secret', 'key', 'token', 'password'])
    
    def compose(self) -> ComposeResult:
        """Compose the variable row."""
        with Horizontal():
            yield Label(self.key, classes="var-key")
            if self.masked and self.is_sensitive:
                yield Label("*" * 20, classes="var-value-masked")
            else:
                yield Label(self.value, classes="var-value")
            yield Button("Edit", variant="primary", classes="var-btn", id=f"edit-{self.key}")
            yield Button("Delete", variant="error", classes="var-btn", id=f"delete-{self.key}")


class VariableEditor(Container):
    """Form for adding/editing variables."""
    
    class VariableSaved(Message):
        """Message sent when a variable is saved."""
        def __init__(self, key: str, value: str):
            self.key = key
            self.value = value
            super().__init__()
    
    class EditorClosed(Message):
        """Message sent when editor is closed."""
        pass
    
    def __init__(self, key: str = "", value: str = "", edit_mode: bool = False):
        super().__init__()
        self.edit_key = key
        self.edit_value = value
        self.edit_mode = edit_mode
    
    def compose(self) -> ComposeResult:
        """Compose the editor form."""
        yield Static("Add/Edit Variable", classes="editor-title")
        yield Label("Key:")
        yield Input(placeholder="TIABLE_NAME", value=self.edit_key, id="var-key-input")
        yield Label("Value:")
        yield Input(placeholder="variable_value", value=self.edit_value, id="var-value-input", password=False)
        with Horizontal():
            yield Button("Save", variant="success", id="save-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            key_input = self.query_one("#var-key-input", Input)
            value_input = self.query_one("#var-value-input", Input)
            
            key = key_input.value.strip()
            value = value_input.value.strip()
            
            if key and value:
                self.post_message(self.VariableSaved(key, value))
        elif event.button.id == "cancel-btn":
            self.post_message(self.EditorClosed())


class VariableList(Container):
    """List displaying all variables with interactive buttons."""
    
    def __init__(self, profile: str, mask: bool = True):
        super().__init__()
        self.profile = profile
        self.mask = mask
        self.manager = EnvManager(profile)
    
    def compose(self) -> ComposeResult:
        """Compose the variable list."""
        with VerticalScroll(classes="variable-list"):
            yield from self._create_variable_rows()
    
    def _create_variable_rows(self, search_term: str = ""):
        """Create VariableRow components for each variable."""
        env_vars = self.manager.list_env(mask=self.mask)
        rows = []

        for key, value in sorted(env_vars.items()):
            # Filter by search term if provided
            if search_term and search_term.lower() not in key.lower():
                continue

            row = VariableRow(key, value, masked=self.mask)
            rows.append(row)

        return rows
    
    def refresh_list(self, search_term: str = "") -> None:
        """Refresh the variable list."""
        # Remove existing rows
        for row in self.query(VariableRow):
            row.remove()

        # Add new rows
        new_rows = self._create_variable_rows(search_term)
        scroll_container = self.query_one(VerticalScroll)
        for row in new_rows:
            scroll_container.mount(row)
    
    def toggle_mask(self) -> None:
        """Toggle masking of sensitive values."""
        self.mask = not self.mask
        self.refresh_list()


class VariablesScreen(Container):
    """Main variables management screen."""
    
    DEFAULT_CSS = """
    VariablesScreen {
        height: 100%;
        overflow-y: auto;
    }

    VariablesScreen .screen-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        height: 3;
    }

    VariablesScreen .stats-bar {
        background: $surface;
        padding: 1 2;
        margin-bottom: 1;
        height: 3;
    }

    VariablesScreen .action-bar {
        height: 3;
        margin-bottom: 1;
    }

    VariablesScreen .action-bar Button {
        margin-right: 1;
    }

    VariablesScreen .content-area {
        height: 1fr;
        overflow-y: auto;
    }

    VariablesScreen .search-input {
        margin-bottom: 1;
    }

    VariablesScreen VariableList {
        height: 1fr;
    }

    VariablesScreen .variable-list {
        height: 1fr;
        padding: 1 2;
    }

    VariablesScreen VariableRow {
        height: 3;
        background: $surface;
        margin-bottom: 1;
        padding: 1;
        align: center middle;
    }

    VariablesScreen VariableRow .var-key {
        width: 30%;
        text-align: left;
        color: $primary;
    }

    VariablesScreen VariableRow .var-value {
        width: 40%;
        text-align: left;
        color: $success;
    }

    VariablesScreen VariableRow .var-value-masked {
        width: 40%;
        text-align: left;
        color: $warning;
    }

    VariablesScreen VariableRow .var-btn {
        width: 15%;
        margin-left: 1;
    }

    VariablesScreen VariableEditor {
        align: center middle;
    }

    VariablesScreen VariableEditor > Container {
        width: 60%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    VariablesScreen .editor-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        height: 2;
    }

    ImportDialog, ExportDialog {
        align: center middle;
    }

    ImportDialog > Container, ExportDialog > Container {
        width: 60%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    ImportDialog .dialog-title, ExportDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        height: 3;
    }

    ImportDialog Label, ExportDialog Label {
        margin-bottom: 1;
    }

    ImportDialog Input, ExportDialog Input {
        margin-bottom: 1;
    }

    ImportDialog .dialog-actions, ExportDialog .dialog-actions {
        height: 3;
        margin-top: 1;
    }

    ImportDialog .dialog-actions Button, ExportDialog .dialog-actions Button {
        margin-right: 1;
    }
    """
    
    def __init__(self, profile: Optional[str] = None):
        super().__init__()
        self.profile = profile or get_current_profile()
        self.manager = EnvManager(self.profile)
        self.show_editor = False
        self.mask_enabled = True
        self.search_visible = False
        self.current_search = ""
    
    def compose(self) -> ComposeResult:
        """Compose the variables screen."""
        # Header
        yield Static(f"Environment Variables - Profile: {self.profile}", classes="screen-title")
        
        # Stats bar
        env_vars = self.manager.load_env()
        stats_text = Text()
        stats_text.append(f"= Total: ", style="#757575")
        stats_text.append(f"{len(env_vars)}", style="bold #00E676")
        stats_text.append(f"  |  [ Sensitive: ", style="#757575")
        sensitive_count = sum(1 for k in env_vars.keys() if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
        stats_text.append(f"{sensitive_count}", style="bold #FFB300")
        yield Static(stats_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("+ Add Variable", variant="success", id="add-var-btn")
            yield Button("v Import", variant="primary", id="import-btn")
            yield Button("^ Export", variant="primary", id="export-btn")
            yield Button("@ Refresh", variant="default", id="refresh-btn")
            yield Button("o Toggle Mask", variant="default", id="toggle-mask-btn")
            yield Button("FvD Search", variant="default", id="search-btn")
        
        # Search bar (initially hidden)
        search_input = Input(placeholder="Search variables...", id="search-input", classes="search-input")
        if not self.search_visible:
            search_input.display = False
        yield search_input
        
        # Main content area
        with Vertical(classes="content-area"):
            # Variable list
            yield VariableList(self.profile, mask=self.mask_enabled)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "add-var-btn":
            self.show_variable_editor()
        elif button_id == "refresh-btn":
            self.refresh_variables()
        elif button_id == "toggle-mask-btn":
            self.toggle_mask()
        elif button_id == "search-btn":
            self.toggle_search()
        elif button_id == "import-btn":
            self.show_import_dialog()
        elif button_id == "export-btn":
            self.show_export_dialog()
        elif button_id and button_id.startswith("edit-"):
            var_key = button_id.replace("edit-", "")
            env_vars = self.manager.load_env()
            if var_key in env_vars:
                self.show_variable_editor(var_key, env_vars[var_key])
        elif button_id and button_id.startswith("delete-"):
            var_key = button_id.replace("delete-", "")
            self.delete_variable(var_key)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.current_search = event.value
            self.refresh_variables()
    
    def show_variable_editor(self, key: str = "", value: str = "") -> None:
        """Show the variable editor."""
        self.run_worker(self._mount_editor(key, value))
    
    async def _mount_editor(self, key: str = "", value: str = "") -> None:
        """Mount the variable editor overlay."""
        try:
            existing = self.query_one(VariableEditor)
            await existing.remove()
        except:
            pass

        editor = VariableEditor(key, value, edit_mode=bool(key))
        await self.mount(editor)
        editor.add_class("overlay")
    
    def on_variable_editor_variable_saved(self, message: VariableEditor.VariableSaved) -> None:
        """Handle variable saved message."""
        try:
            self.manager.add_env(message.key, message.value)
            self.app.notify(f"+ Saved variable: {message.key}", severity="information")
            self.run_worker(self._remove_editor())
            self.refresh_variables()
        except Exception as e:
            self.app.notify(f"Failed to save variable: {e}", severity="error")
    
    def on_variable_editor_editor_closed(self, message: VariableEditor.EditorClosed) -> None:
        """Handle editor closed message."""
        self.run_worker(self._remove_editor())
    
    async def _remove_editor(self) -> None:
        """Remove the variable editor overlay."""
        try:
            editor = self.query_one(VariableEditor)
            await editor.remove()
        except:
            pass
    
    def delete_variable(self, key: str) -> None:
        """Delete a variable."""
        try:
            self.manager.remove_env(key)
            self.app.notify(f"+ Deleted variable: {key}", severity="information")
            self.refresh_variables()
        except Exception as e:
            self.app.notify(f"Failed to delete variable: {e}", severity="error")
    
    def refresh_variables(self) -> None:
        """Refresh the variable list."""
        var_list = self.query_one(VariableList)
        var_list.refresh_list(search_term=self.current_search)

        # Update stats
        env_vars = self.manager.load_env()

        # Count filtered results if searching
        if self.current_search:
            filtered_count = sum(1 for k in env_vars.keys() if self.current_search.lower() in k.lower())
            stats_text = Text()
            stats_text.append(f"= Showing: ", style="#757575")
            stats_text.append(f"{filtered_count}", style="bold #00E676")
            stats_text.append(f" / {len(env_vars)}", style="#757575")
        else:
            stats_text = Text()
            stats_text.append(f"= Total: ", style="#757575")
            stats_text.append(f"{len(env_vars)}", style="bold #00E676")
            stats_text.append(f"  |  [ Sensitive: ", style="#757575")
            sensitive_count = sum(1 for k in env_vars.keys() if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
            stats_text.append(f"{sensitive_count}", style="bold #FFB300")

        stats_bar = self.query_one(".stats-bar", Static)
        stats_bar.update(stats_text)
    
    def toggle_mask(self) -> None:
        """Toggle masking of sensitive values."""
        self.mask_enabled = not self.mask_enabled
        var_list = self.query_one(VariableList)
        var_list.toggle_mask()
    
    def toggle_search(self) -> None:
        """Toggle search input visibility."""
        search_input = self.query_one("#search-input", Input)
        self.search_visible = not self.search_visible
        search_input.display = self.search_visible
        if self.search_visible:
            search_input.focus()
        else:
            # Clear search when hiding
            search_input.value = ""
            self.current_search = ""
            self.refresh_variables()
    
    def show_import_dialog(self) -> None:
        """Show import dialog."""
        self.app.push_screen(ImportDialog(self.manager, self.refresh_variables))

    def show_export_dialog(self) -> None:
        """Show export dialog."""
        self.app.push_screen(ExportDialog(self.manager))


class ImportDialog(ModalScreen):
    """Modal dialog for importing variables."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, manager: EnvManager, on_success_callback):
        super().__init__()
        self.manager = manager
        self.on_success_callback = on_success_callback

    def compose(self) -> ComposeResult:
        """Compose the import dialog."""
        with Vertical():
            yield Static("📥 Import Variables", classes="dialog-title")
            
            yield Label("Select file to import:")
            yield Input(
                placeholder="Enter path to file (e.g., /path/to/env.json or /path/to/.env)",
                id="import-file-input"
            )
            
            yield Label("Import format:")
            yield Input(
                placeholder="env, json, or yaml",
                value="auto",
                id="import-format-input"
            )
            
            yield Label("Import mode:")
            yield Input(
                placeholder="merge (add new, keep existing) or replace (overwrite all)",
                value="merge",
                id="import-mode-input"
            )
            
            with Horizontal(classes="dialog-actions"):
                yield Button("📥 Import", id="confirm-import-btn", variant="success")
                yield Button("❌ Cancel", id="cancel-import-btn", variant="error")
    
    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "confirm-import-btn":
            self._perform_import()
        elif button_id == "cancel-import-btn":
            self.dismiss()
    
    def _perform_import(self) -> None:
        """Perform the import operation."""
        try:
            file_input = self.query_one("#import-file-input", Input)
            format_input = self.query_one("#import-format-input", Input)
            mode_input = self.query_one("#import-mode-input", Input)
            
            file_path = file_input.value.strip()
            format_type = format_input.value.strip().lower() or "auto"
            import_mode = mode_input.value.strip().lower() or "merge"
            
            if not file_path:
                self.notify("Please enter a file path", severity="error")
                return
            
            # Convert to Path object
            path = Path(file_path)
            if not path.exists():
                self.notify(f"File not found: {file_path}", severity="error")
                return
            
            # Auto-detect format if not specified
            if format_type == "auto":
                if path.suffix.lower() in ['.json']:
                    format_type = "json"
                elif path.suffix.lower() in ['.yaml', '.yml']:
                    format_type = "yaml"
                elif path.name.startswith('.env') or path.name.lower() == '.env':
                    format_type = "env"
                else:
                    # Try to detect by content
                    try:
                        with open(path, 'r') as f:
                            content = f.read().strip()
                            if content.startswith('{') or content.startswith('['):
                                format_type = "json"
                            elif '=' in content and '\n' in content:
                                format_type = "env"
                            else:
                                format_type = "env"  # default
                    except:
                        format_type = "env"  # fallback
            
            # Perform import based on mode
            if import_mode == "replace":
                # Load all variables from file
                if format_type == "json":
                    with open(path, 'r') as f:
                        imported_vars = json.load(f)
                elif format_type == "yaml":
                    try:
                        import yaml
                        with open(path, 'r') as f:
                            imported_vars = yaml.safe_load(f)
                    except ImportError:
                        self.notify("PyYAML not installed - cannot import YAML files", severity="error")
                        return
                else:  # env format
                    imported_vars = {}
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                imported_vars[key.strip()] = value.strip()
                
                # Save all imported variables (replace mode)
                self.manager.save_env(imported_vars)
                self.notify(f"✓ Imported {len(imported_vars)} variables from {file_path} (replace mode)", severity="information")
                
            else:  # merge mode
                # Load existing variables
                existing_vars = self.manager.load_env()
                
                # Load variables from file
                if format_type == "json":
                    with open(path, 'r') as f:
                        imported_vars = json.load(f)
                elif format_type == "yaml":
                    try:
                        import yaml
                        with open(path, 'r') as f:
                            imported_vars = yaml.safe_load(f)
                    except ImportError:
                        self.notify("PyYAML not installed - cannot import YAML files", severity="error")
                        return
                else:  # env format
                    imported_vars = {}
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                imported_vars[key.strip()] = value.strip()
                
                # Merge: imported vars override existing ones
                merged_vars = {**existing_vars, **imported_vars}
                self.manager.save_env(merged_vars)
                
                new_count = len(imported_vars)
                self.notify(f"✓ Imported {new_count} variables from {file_path} (merge mode)", severity="information")
            
            # Call success callback
            self.on_success_callback()
            
            # Close modal
            self.dismiss()
            
        except Exception as e:
            self.notify(f"Import failed: {e}", severity="error")


class ExportDialog(ModalScreen):
    """Modal dialog for exporting variables."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, manager: EnvManager):
        super().__init__()
        self.manager = manager

    def compose(self) -> ComposeResult:
        """Compose the export dialog."""
        with Vertical():
            yield Static("📤 Export Variables", classes="dialog-title")
            
            yield Label("Select export location:")
            yield Input(
                placeholder="Enter path to export file (e.g., /path/to/env_export.json)",
                id="export-file-input"
            )
            
            yield Label("Export format:")
            yield Input(
                placeholder="env, json, or yaml",
                value="json",
                id="export-format-input"
            )
            
            yield Label("Export options:")
            yield Input(
                placeholder="mask (hide sensitive values) or show (include all values)",
                value="mask",
                id="export-options-input"
            )
            
            with Horizontal(classes="dialog-actions"):
                yield Button("📤 Export", id="confirm-export-btn", variant="success")
                yield Button("❌ Cancel", id="cancel-export-btn", variant="error")
    
    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "confirm-export-btn":
            self._perform_export()
        elif button_id == "cancel-export-btn":
            self.dismiss()
    
    def _perform_export(self) -> None:
        """Perform the export operation."""
        try:
            file_input = self.query_one("#export-file-input", Input)
            format_input = self.query_one("#export-format-input", Input)
            options_input = self.query_one("#export-options-input", Input)
            
            file_path = file_input.value.strip()
            export_format = format_input.value.strip().lower() or "json"
            export_options = options_input.value.strip().lower() or "mask"
            
            if not file_path:
                self.notify("Please enter a file path", severity="error")
                return
            
            # Convert to Path object and ensure directory exists
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get variables to export
            if export_options == "show":
                variables = self.manager.load_env()
            else:  # mask
                variables = self.manager.list_env(mask=True)
            
            # Export based on format
            if export_format == "json":
                with open(path, 'w') as f:
                    json.dump(variables, f, indent=2)
            elif export_format == "yaml":
                try:
                    import yaml
                    with open(path, 'w') as f:
                        yaml.dump(variables, f, default_flow_style=False)
                except ImportError:
                    self.notify("PyYAML not installed - cannot export to YAML files", severity="error")
                    return
            else:  # env format
                with open(path, 'w') as f:
                    f.write(f"# Environment variables export\n")
                    f.write(f"# Generated by EnvCLI\n\n")
                    for key, value in sorted(variables.items()):
                        f.write(f"{key}={value}\n")
            
            # Check if file was created
            if path.exists():
                file_size = path.stat().st_size
                self.notify(f"✓ Exported {len(variables)} variables to {file_path} ({file_size} bytes)", severity="information")
            else:
                self.notify("Export failed - file was not created", severity="error")
            
            # Close modal
            self.dismiss()
            
        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error")
