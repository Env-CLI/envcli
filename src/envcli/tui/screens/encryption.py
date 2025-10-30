"""
Encryption screen for EnvCLI TUI
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, Input
from textual.message import Message
from rich.text import Text

from ...encryption import encrypt_file, decrypt_file, get_or_create_key, KEY_FILE
from ...config import get_current_profile, PROFILES_DIR
from ...env_manager import EnvManager


class FileSelector(Container):
    """File selector for encryption/decryption."""
    
    class FileSelected(Message):
        """Message sent when a file is selected."""
        def __init__(self, file_path: str, operation: str):
            self.file_path = file_path
            self.operation = operation
            super().__init__()
    
    class SelectorClosed(Message):
        """Message sent when selector is closed."""
        pass
    
    def __init__(self, operation: str = "encrypt"):
        super().__init__()
        self.operation = operation  # "encrypt" or "decrypt"
    
    def compose(self) -> ComposeResult:
        """Compose the file selector."""
        title = "Encrypt File" if self.operation == "encrypt" else "Decrypt File"
        yield Static(title, classes="selector-title")
        
        yield Label("File Path:")
        yield Input(placeholder="/path/to/file", id="file-path-input")
        
        # Quick select buttons for profile files
        yield Static("Quick Select Profile Files:", classes="quick-select-label")

        with Vertical(classes="quick-select-list"):
            # List profile files
            profiles_dir = PROFILES_DIR
            if profiles_dir.exists():
                for profile_file in sorted(profiles_dir.glob("*.json")):
                    # Replace dots with dashes for valid IDs
                    safe_id = profile_file.name.replace(".", "-")
                    yield Button(f"📄 {profile_file.name}", id=f"select-{safe_id}", variant="default")
        
        # Action buttons
        with Horizontal(classes="selector-actions"):
            yield Button("Confirm", variant="success", id="confirm-file-btn")
            yield Button("Cancel", variant="default", id="cancel-file-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "confirm-file-btn":
            file_input = self.query_one("#file-path-input", Input)
            file_path = file_input.value.strip()
            if file_path:
                self.post_message(self.FileSelected(file_path, self.operation))
            else:
                self.app.notify("Please enter a file path", severity="error")
        elif button_id == "cancel-file-btn":
            self.post_message(self.SelectorClosed())
        elif button_id and button_id.startswith("select-"):
            # Quick select a profile file
            # Convert safe ID back to filename (replace first dash after "select-" back to dot)
            safe_name = button_id.replace("select-", "")
            # Find the profile file that matches
            profiles_dir = PROFILES_DIR
            for profile_file in profiles_dir.glob("*.json"):
                if profile_file.name.replace(".", "-") == safe_name:
                    file_path = str(profile_file)
                    file_input = self.query_one("#file-path-input", Input)
                    file_input.value = file_path
                    break


class KeyManager(Container):
    """Key management interface."""
    
    class KeyRegenerated(Message):
        """Message sent when key is regenerated."""
        pass
    
    class ManagerClosed(Message):
        """Message sent when manager is closed."""
        pass
    
    def compose(self) -> ComposeResult:
        """Compose the key manager."""
        yield Static("Encryption Key Management", classes="manager-title")
        
        # Show key info
        info = Text()
        info.append("!️ Warning: ", style="bold #FFB300")
        info.append("Regenerating the key will make all previously encrypted files unreadable!\n\n", style="#FFB300")
        info.append("Current key location: ", style="#757575")
        info.append(str(KEY_FILE), style="#64FFDA")
        yield Static(info, classes="key-info")
        
        # Key status
        if KEY_FILE.exists():
            status = Text()
            status.append("+ Encryption key exists\n", style="bold #00E676")
            status.append(f"Key file size: {KEY_FILE.stat().st_size} bytes", style="#757575")
            yield Static(status, classes="key-status")
        else:
            status = Text()
            status.append("X No encryption key found\n", style="bold #FF5252")
            status.append("A new key will be generated on first use", style="#757575")
            yield Static(status, classes="key-status")
        
        # Action buttons
        with Horizontal(classes="manager-actions"):
            yield Button("@ Regenerate Key", variant="error", id="regenerate-key-btn")
            yield Button("- Show Key Path", variant="default", id="show-key-path-btn")
            yield Button("Close", variant="default", id="close-manager-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "regenerate-key-btn":
            self.regenerate_key()
        elif button_id == "show-key-path-btn":
            self.app.notify(f"Key path: {KEY_FILE}", severity="information")
        elif button_id == "close-manager-btn":
            self.post_message(self.ManagerClosed())
    
    def regenerate_key(self) -> None:
        """Regenerate the encryption key."""
        try:
            # Delete existing key
            if KEY_FILE.exists():
                KEY_FILE.unlink()
            
            # Generate new key
            get_or_create_key()
            
            self.app.notify("+ New encryption key generated", severity="information")
            self.post_message(self.KeyRegenerated())
        except Exception as e:
            self.app.notify(f"Failed to regenerate key: {e}", severity="error")


class EncryptionScreen(Container):
    """Main encryption screen."""
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
    
    def compose(self) -> ComposeResult:
        """Compose the encryption screen."""
        # Header
        yield Static("[ Encryption & Security", classes="screen-title")
        
        # Status bar
        status_text = Text()
        status_text.append("/ Profile: ", style="#757575")
        status_text.append(self.current_profile, style="bold #00E676")
        status_text.append("  |  🔑 Key: ", style="#757575")
        if KEY_FILE.exists():
            status_text.append("+ Exists", style="bold #00E676")
        else:
            status_text.append("X Not Found", style="bold #FF5252")
        yield Static(status_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("[ Encrypt File", variant="success", id="encrypt-file-btn")
            yield Button("🔓 Decrypt File", variant="primary", id="decrypt-file-btn")
            yield Button("🔑 Manage Key", variant="default", id="manage-key-btn")
            yield Button("= Check Status", variant="default", id="check-status-btn")
        
        # Main content area
        with Vertical(classes="content-area"):
            with VerticalScroll(classes="encryption-info", id="info-container"):
                yield from self._create_info_display()
    
    def _create_info_display(self):
        """Create the information display."""
        # Encryption info
        info = Text()
        info.append("🔐 Encryption Method\n", style="bold #00E676")
        info.append("Algorithm: ", style="#757575")
        info.append("Fernet (AES-128-CBC + HMAC)\n", style="#64FFDA")
        info.append("Key Size: ", style="#757575")
        info.append("256 bits\n\n", style="#64FFDA")
        
        info.append("📝 How It Works\n", style="bold #00E676")
        info.append("• Files are encrypted in-place (original is replaced)\n", style="#E0E0E0")
        info.append("• Encryption key is stored in: ", style="#E0E0E0")
        info.append(f"{KEY_FILE}\n", style="#64FFDA")
        info.append("• Keep your key safe - without it, files cannot be decrypted\n", style="#E0E0E0")
        info.append("• Recommended: Backup your key to a secure location\n\n", style="#FFB300")
        
        info.append("!️ Important Notes\n", style="bold #FFB300")
        info.append("• Always backup files before encrypting\n", style="#FFB300")
        info.append("• Encrypted files cannot be read without the key\n", style="#FFB300")
        info.append("• Regenerating the key makes old encrypted files unreadable\n", style="#FFB300")
        
        yield Static(info, classes="encryption-info-text")
        
        # Profile encryption status
        yield Static("\n= Profile Files Status", classes="section-title")
        
        profiles_dir = PROFILES_DIR
        if profiles_dir.exists():
            for profile_file in sorted(profiles_dir.glob("*.json")):
                status = self._check_file_encryption_status(profile_file)
                status_text = Text()
                status_text.append(f"📄 {profile_file.name}: ", style="#64FFDA")
                if status == "encrypted":
                    status_text.append("[ Encrypted", style="#00E676")
                elif status == "plain":
                    status_text.append("🔓 Plain Text", style="#FFB300")
                else:
                    status_text.append("❓ Unknown", style="#757575")
                yield Static(status_text, classes="file-status")
    
    def _check_file_encryption_status(self, file_path: Path) -> str:
        """Check if a file is encrypted."""
        try:
            content = file_path.read_bytes()
            # Try to decode as JSON (plain text)
            import json
            json.loads(content.decode('utf-8'))
            return "plain"
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If it fails, it's likely encrypted
            return "encrypted"
        except Exception:
            return "unknown"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "encrypt-file-btn":
            self.show_file_selector("encrypt")
        elif button_id == "decrypt-file-btn":
            self.show_file_selector("decrypt")
        elif button_id == "manage-key-btn":
            self.show_key_manager()
        elif button_id == "check-status-btn":
            self.run_worker(self.refresh_status())
    
    def show_file_selector(self, operation: str) -> None:
        """Show the file selector."""
        self.run_worker(self._mount_selector(operation))
    
    async def _mount_selector(self, operation: str) -> None:
        """Mount the file selector overlay."""
        try:
            existing = self.query_one(FileSelector)
            await existing.remove()
        except:
            pass
        
        selector = FileSelector(operation)
        await self.mount(selector)
        selector.add_class("overlay")
    
    def show_key_manager(self) -> None:
        """Show the key manager."""
        self.run_worker(self._mount_key_manager())
    
    async def _mount_key_manager(self) -> None:
        """Mount the key manager overlay."""
        try:
            existing = self.query_one(KeyManager)
            await existing.remove()
        except:
            pass
        
        manager = KeyManager()
        await self.mount(manager)
        manager.add_class("overlay")
    
    def on_file_selector_file_selected(self, message: FileSelector.FileSelected) -> None:
        """Handle file selected message."""
        self.run_worker(self._process_file(message.file_path, message.operation))
        self.run_worker(self._remove_selector())
    
    def on_file_selector_selector_closed(self, message: FileSelector.SelectorClosed) -> None:
        """Handle selector closed message."""
        self.run_worker(self._remove_selector())
    
    async def _remove_selector(self) -> None:
        """Remove the file selector overlay."""
        try:
            selector = self.query_one(FileSelector)
            await selector.remove()
        except:
            pass
    
    async def _process_file(self, file_path: str, operation: str) -> None:
        """Process file encryption/decryption."""
        try:
            if operation == "encrypt":
                self.app.notify(f"Encrypting {file_path}...", severity="information")
                encrypt_file(file_path)
                self.app.notify(f"+ Encrypted {file_path}", severity="information")
            else:
                self.app.notify(f"Decrypting {file_path}...", severity="information")
                decrypt_file(file_path)
                self.app.notify(f"+ Decrypted {file_path}", severity="information")
            
            # Refresh status display
            await self.refresh_status()
        except FileNotFoundError:
            self.app.notify(f"File not found: {file_path}", severity="error")
        except ValueError as e:
            self.app.notify(f"Decryption failed: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Operation failed: {e}", severity="error")
    
    def on_key_manager_key_regenerated(self, message: KeyManager.KeyRegenerated) -> None:
        """Handle key regenerated message."""
        self.run_worker(self._remove_key_manager())
        self.run_worker(self.refresh_status())
    
    def on_key_manager_manager_closed(self, message: KeyManager.ManagerClosed) -> None:
        """Handle manager closed message."""
        self.run_worker(self._remove_key_manager())
    
    async def _remove_key_manager(self) -> None:
        """Remove the key manager overlay."""
        try:
            manager = self.query_one(KeyManager)
            await manager.remove()
        except:
            pass
    
    async def refresh_status(self) -> None:
        """Refresh the status display."""
        try:
            # Update status bar
            status_text = Text()
            status_text.append("/ Profile: ", style="#757575")
            status_text.append(self.current_profile, style="bold #00E676")
            status_text.append("  |  🔑 Key: ", style="#757575")
            if KEY_FILE.exists():
                status_text.append("+ Exists", style="bold #00E676")
            else:
                status_text.append("X Not Found", style="bold #FF5252")
            
            stats_bar = self.query_one(".stats-bar", Static)
            stats_bar.update(status_text)
            
            # Refresh info display
            container = self.query_one("#info-container", VerticalScroll)
            await container.remove_children()
            for widget in self._create_info_display():
                await container.mount(widget)
            
            self.app.notify("+ Status refreshed", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to refresh status: {e}", severity="error")

