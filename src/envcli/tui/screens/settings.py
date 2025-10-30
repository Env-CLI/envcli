"""
Settings screen for EnvCLI TUI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, Input, Select
from textual.message import Message
from rich.text import Text

from ...config import load_config, save_config, is_analytics_enabled, set_analytics_enabled, CONFIG_FILE
from ...ai_assistant import AIAssistant


class AIProviderConfig(Container):
    """AI provider configuration dialog."""

    class ProviderConfigured(Message):
        """Message sent when provider is configured."""
        def __init__(self, provider: str, model: str = None):
            self.provider = provider
            self.model = model
            super().__init__()

    class ConfigClosed(Message):
        """Message sent when config is closed."""
        pass

    def __init__(self):
        super().__init__()
        self.ai = AIAssistant()

    def compose(self) -> ComposeResult:
        """Compose the AI config dialog."""
        yield Static("* Configure AI Provider", classes="config-title")

        with VerticalScroll(id="config-scroll"):
            # Current status
            status = Text()
            status.append("Current Status: ", style="#757575")
            if self.ai.enabled:
                status.append("+ Enabled", style="bold #00E676")
                status.append(f"\nProvider: ", style="#757575")
                status.append(self.ai.config.get("provider", "unknown"), style="#64FFDA")
                if self.ai.config.get("model"):
                    status.append(f"\nModel: ", style="#757575")
                    status.append(self.ai.config.get("model"), style="#64FFDA")
            else:
                status.append("X Disabled", style="bold #FF5252")
            yield Static(status, classes="ai-status")

            # Provider selection
            yield Label("Select Provider:")
            with Vertical(classes="provider-list"):
                yield Button("FvD Pattern Matching (Local, No API Key)", id="provider-pattern", variant="default")
                yield Button("* OpenAI (GPT-4, GPT-3.5)", id="provider-openai", variant="default")
                yield Button("BRAv Anthropic (Claude)", id="provider-anthropic", variant="default")
                yield Button("O Google (Gemini)", id="provider-google", variant="default")
                yield Button("@ Ollama (Local LLMs)", id="provider-ollama", variant="default")

            # Model input (for providers that need it)
            yield Label("Model (optional):")
            yield Input(placeholder="e.g., gpt-4o-mini, claude-3-5-sonnet-20241022", id="model-input")

            # Info
            info = Text()
            info.append("vFO ", style="#2196F3")
            info.append("Pattern Matching requires no setup. Other providers need API keys set as environment variables.", style="#757575")
            yield Static(info, classes="config-info")

        # Action buttons (outside scroll, always visible)
        with Horizontal(classes="config-actions"):
            yield Button("Enable AI", variant="success", id="enable-ai-btn")
            yield Button("Disable AI", variant="error", id="disable-ai-btn")
            yield Button("Close", variant="default", id="close-config-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id and button_id.startswith("provider-"):
            provider = button_id.replace("provider-", "")
            self.selected_provider = provider
            self.app.notify(f"Selected provider: {provider}", severity="information")
        elif button_id == "enable-ai-btn":
            self.enable_ai()
        elif button_id == "disable-ai-btn":
            self.disable_ai()
        elif button_id == "close-config-btn":
                self.app.log("Close button clicked")
                # Directly call parent's close method
                try:
                    parent = self.parent
                    if hasattr(parent, 'close_ai_config'):
                        self.app.log("Calling parent.close_ai_config()")
                        parent.close_ai_config()
                    else:
                        self.app.log("Parent doesn't have close_ai_config method")
                except Exception as e:
                    self.app.log(f"Direct parent call failed: {e}")
        self.app.notify("Closing configuration...", severity="information")
    
    def enable_ai(self) -> None:
        """Enable AI with selected provider."""
        try:
            provider = getattr(self, 'selected_provider', 'pattern-matching')
            model_input = self.query_one("#model-input", Input)
            model = model_input.value.strip() or None
            
            self.ai.enable_ai(provider=provider, model=model)
            self.app.notify(f"+ AI enabled with {provider}", severity="information")
            self.post_message(self.ProviderConfigured(provider, model))
        except Exception as e:
            self.app.notify(f"Failed to enable AI: {e}", severity="error")
    
    def disable_ai(self) -> None:
        """Disable AI features."""
        try:
            self.ai.disable_ai()
            self.app.notify("+ AI disabled", severity="information")
            self.post_message(self.ConfigClosed())
        except Exception as e:
            self.app.notify(f"Failed to disable AI: {e}", severity="error")


class SettingsScreen(Container):
    """Main settings screen."""
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.ai = AIAssistant()
        self.refreshing = False  # Guard against multiple simultaneous refreshes
    
    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        # Header
        yield Static("# Settings & Preferences", classes="screen-title")

        # Main content
        with VerticalScroll(classes="content-area", id="settings-content"):
            yield from self._create_settings_widgets()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Test refresh functionality
        self.app.log("Settings screen mounted, testing refresh...")
        # Don't auto-refresh for now, let the user trigger it

    def _create_settings_widgets(self):
        """Create the settings widgets (generator)."""
        # AI Settings Section
        yield Static("* AI Configuration", classes="section-header")
        
        ai_info = Text()
        ai_info.append("Status: ", style="#757575")
        if self.ai.enabled:
            ai_info.append("+ Enabled\n", style="bold #00E676")
            ai_info.append("Provider: ", style="#757575")
            ai_info.append(self.ai.config.get("provider", "unknown"), style="#64FFDA")
            if self.ai.config.get("model"):
                ai_info.append(f"\nModel: ", style="#757575")
                ai_info.append(self.ai.config.get("model"), style="#64FFDA")
        else:
            ai_info.append("X Disabled", style="bold #FF5252")
        yield Static(ai_info, classes="setting-value")
        
        # AI Configuration Actions
        yield Horizontal(
            Button("* Configure AI Provider", variant="primary", id="config-ai-btn"),
            classes="setting-actions"
        )
        
        yield Static("", classes="section-divider")
        
        # Profile Settings Section
        yield Static("/ Profile Settings", classes="section-header")
        
        profile_info = Text()
        profile_info.append("Default Profile: ", style="#757575")
        profile_info.append(self.config.get("default_profile", "dev"), style="#64FFDA")
        profile_info.append("\nCurrent Profile: ", style="#757575")
        profile_info.append(self.config.get("current_profile", "dev"), style="#64FFDA")
        profile_info.append("\nRemember Last Profile: ", style="#757575")
        remember = self.config.get("remember_last_profile", True)
        profile_info.append("+ Yes" if remember else "X No", style="#00E676" if remember else "#FF5252")
        yield Static(profile_info, classes="setting-value")
        
        # Profile Settings Actions
        yield Horizontal(
            Button("Toggle Remember Last", variant="default", id="toggle-remember-btn"),
            classes="setting-actions"
        )
        
        yield Static("", classes="section-divider")
        
        # Analytics Settings Section
        yield Static("= Analytics & Telemetry", classes="section-header")
        
        analytics_info = Text()
        analytics_info.append("Command Analytics: ", style="#757575")
        analytics_enabled = is_analytics_enabled()
        analytics_info.append("+ Enabled" if analytics_enabled else "X Disabled", 
                             style="bold #00E676" if analytics_enabled else "bold #FF5252")
        analytics_info.append("\n\nvFO ", style="#2196F3")
        analytics_info.append("Analytics tracks command usage for insights. No data is sent externally.", style="#757575")
        yield Static(analytics_info, classes="setting-value")
        
        # Analytics Settings Actions
        yield Horizontal(
            Button("Toggle Analytics", variant="default", id="toggle-analytics-btn"),
            classes="setting-actions"
        )
        
        yield Static("", classes="section-divider")

        # Theme Section
        yield Static("◵ Theme", classes="section-header")

        from ..themes import ThemeManager
        from ...config import CONFIG_DIR
        theme_manager = ThemeManager(CONFIG_DIR)
        current_theme = theme_manager.get_current_theme()

        theme_info = Text()
        theme_info.append("Current Theme: ", style="#757575")
        theme_info.append(current_theme.replace("_", " ").title(), style="#64FFDA")
        theme_info.append("\n\nvFO ", style="#2196F3")
        theme_info.append(f"Choose from {len(theme_manager.get_available_themes())} beautiful themes. Restart required after changing theme.", style="#757575")
        yield Static(theme_info, classes="setting-value")

        # Theme Actions
        yield Horizontal(
            Button("Change Theme", variant="primary", id="change-theme-btn"),
            classes="setting-actions"
        )

        yield Static("", classes="section-divider")

        # System Information Section
        yield Static("[ System Information", classes="section-header")
        
        system_info = Text()
        system_info.append("Config Directory: ", style="#757575")
        system_info.append(str(CONFIG_FILE.parent), style="#64FFDA")
        system_info.append("\nConfig File: ", style="#757575")
        system_info.append(str(CONFIG_FILE), style="#64FFDA")
        
        # Count profiles
        try:
            from ...config import list_profiles
            profiles = list_profiles()
            system_info.append(f"\nTotal Profiles: ", style="#757575")
            system_info.append(str(len(profiles)), style="#64FFDA")
        except Exception as e:
            self.app.log(f"Error counting profiles: {e}")
            system_info.append(f"\nTotal Profiles: ", style="#757575")
            system_info.append("Error", style="#FF5252")
        
        yield Static(system_info, classes="setting-value")
        
        # System Information Actions
        yield Horizontal(
            Button("📂 Open Config Directory", variant="default", id="open-config-btn"),
            Button("@ Refresh Settings", variant="default", id="refresh-settings-btn"),
            classes="setting-actions"
        )
        
        yield Static("", classes="section-divider")
        
        # About Section
        yield Static("vFO About EnvCLI", classes="section-header")
        
        about_info = Text()
        about_info.append("EnvCLI v3.0.0\n", style="bold #00E676")
        about_info.append("Advanced Environment Variable Management\n\n", style="#64FFDA")
        about_info.append("Features:\n", style="bold #757575")
        about_info.append("• Multi-profile management\n", style="#E0E0E0")
        about_info.append("• AI-powered analysis\n", style="#E0E0E0")
        about_info.append("• Cloud sync (AWS, Azure, GCP, Vault, GitHub, K8s)\n", style="#E0E0E0")
        about_info.append("• File encryption\n", style="#E0E0E0")
        about_info.append("• Custom rules & policies\n", style="#E0E0E0")
        about_info.append("• Interactive TUI\n", style="#E0E0E0")
        yield Static(about_info, classes="setting-value")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "config-ai-btn":
            self.show_ai_config()
        elif button_id == "change-theme-btn":
            self.show_theme_selector()
        elif button_id == "toggle-remember-btn":
            self.toggle_remember_last()
        elif button_id == "toggle-analytics-btn":
            self.toggle_analytics()
        elif button_id == "open-config-btn":
            self.open_config_directory()
        elif button_id == "refresh-settings-btn":
            self.run_worker(self.refresh_settings())
    
    def show_ai_config(self) -> None:
        """Show AI configuration dialog."""
        self.run_worker(self._mount_ai_config())

    def show_theme_selector(self) -> None:
        """Show theme selector."""
        from .theme_selector import ThemeSelector
        self.app.push_screen(ThemeSelector())

    def close_ai_config(self) -> None:
        """Close AI configuration dialog."""
        self.run_worker(self._remove_ai_config())
    
    async def _mount_ai_config(self) -> None:
        """Mount the AI config overlay."""
        try:
            existing = self.query_one(AIProviderConfig)
            await existing.remove()
        except:
            pass
        
        config_dialog = AIProviderConfig()
        await self.mount(config_dialog)
        config_dialog.add_class("overlay")
    
    def on_ai_provider_config_provider_configured(self, message: AIProviderConfig.ProviderConfigured) -> None:
        """Handle provider configured message."""
        self.run_worker(self._remove_ai_config())
        self.run_worker(self.refresh_settings())
    
    def on_ai_provider_config_config_closed(self, message: AIProviderConfig.ConfigClosed) -> None:
        """Handle config closed message."""
        self.app.log("Received ConfigClosed message, removing dialog")
        self.run_worker(self._remove_ai_config())
    
    async def _remove_ai_config(self) -> None:
        """Remove the AI config overlay."""
        try:
            # Query for all AIProviderConfig instances
            dialogs = self.query(AIProviderConfig)
            self.app.log(f"Found {len(dialogs)} config dialog(s)")

            for dialog in dialogs:
                self.app.log(f"Removing dialog: {dialog}")
                await dialog.remove()
                self.app.log(f"Dialog removed successfully")

            self.app.notify("Configuration closed", severity="information")
        except Exception as e:
            import traceback
            self.app.log(f"Failed to remove config dialog: {e}")
            self.app.log(f"Traceback: {traceback.format_exc()}")
            self.app.notify(f"Error closing dialog: {e}", severity="error")
    
    def toggle_remember_last(self) -> None:
        """Toggle remember last profile setting."""
        try:
            self.config = load_config()
            current = self.config.get("remember_last_profile", True)
            self.config["remember_last_profile"] = not current
            save_config(self.config)
            
            status = "enabled" if not current else "disabled"
            self.app.notify(f"+ Remember last profile {status}", severity="information")
            self.run_worker(self.refresh_settings())
        except Exception as e:
            self.app.notify(f"Failed to toggle setting: {e}", severity="error")
    
    def toggle_analytics(self) -> None:
        """Toggle analytics setting."""
        try:
            current = is_analytics_enabled()
            set_analytics_enabled(not current)
            
            status = "enabled" if not current else "disabled"
            self.app.notify(f"+ Analytics {status}", severity="information")
            self.run_worker(self.refresh_settings())
        except Exception as e:
            self.app.notify(f"Failed to toggle analytics: {e}", severity="error")
    
    def open_config_directory(self) -> None:
        """Open config directory in file manager."""
        import subprocess
        import platform
        
        try:
            config_dir = str(CONFIG_FILE.parent)
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["open", config_dir])
            elif system == "Windows":
                subprocess.run(["explorer", config_dir])
            else:  # Linux
                subprocess.run(["xdg-open", config_dir])
            
            self.app.notify(f"+ Opened {config_dir}", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to open directory: {e}", severity="error")
    
    async def refresh_settings(self) -> None:
        """Refresh the settings display."""
        if self.refreshing:
            self.app.log("Refresh already in progress, skipping")
            return
        
        self.refreshing = True
        self.refreshing = True
        try:
            self.app.log("Starting settings refresh...")
            # Reload config and AI
            self.config = load_config()
            self.ai = AIAssistant()
            self.app.log("Config and AI reloaded")

            # Refresh content
            try:
                container = self.query_one("#settings-content", VerticalScroll)
                self.app.log(f"Found container: {container}")
            except Exception as e:
                self.app.log(f"Failed to find settings container: {e}")
                self.app.notify("Settings container not found", severity="error")
                return

            # Remove existing children safely
            try:
                await container.remove_children()
                self.app.log("Children removed successfully")
            except Exception as e:
                self.app.log(f"Failed to remove children: {e}")
                self.app.notify(f"Failed to clear settings: {e}", severity="error")
                return

            # Mount new widgets
            widget_count = 0
            try:
                widgets_to_mount = list(self._create_settings_widgets())  # Convert generator to list
                self.app.log(f"Generated {len(widgets_to_mount)} widgets to mount")

                for widget in widgets_to_mount:
                    widget_count += 1
                    self.app.log(f"Mounting widget {widget_count}: {type(widget).__name__}")
                    await container.mount(widget)

                self.app.log(f"Mounted {widget_count} widgets successfully")
                self.app.notify("+ Settings refreshed", severity="information")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.app.log(f"Failed to mount widgets: {e}")
                self.app.log(f"Full traceback:\\n{error_details}")
                self.app.notify(f"Failed to refresh settings: {e}", severity="error")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.app.notify(f"Failed to refresh settings: {e}", severity="error")
            self.app.log(f"Settings refresh error: {e}")
            self.app.log(f"Full traceback:\\n{error_details}")

        finally:
            self.refreshing = False
