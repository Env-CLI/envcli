"""
Encryption screen for EnvCLI TUI
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, Label, Input
from textual.message import Message
from textual.screen import ModalScreen
from rich.text import Text

from ...encryption import encrypt_file, decrypt_file, get_or_create_key, KEY_FILE
from ...config import get_current_profile, PROFILES_DIR
from ...env_manager import EnvManager


class FileSelector(Container):
    """File selector for encryption/decryption."""

    DEFAULT_CSS = """
    FileSelector {
        width: 80;
        height: auto;
        max-height: 40;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    FileSelector.overlay {
        align: center middle;
        layer: overlay;
    }

    .selector-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .quick-select-label {
        margin-top: 1;
        margin-bottom: 1;
        color: $text-muted;
    }

    .quick-select-list {
        height: auto;
        max-height: 15;
        overflow-y: auto;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    .quick-select-list Button {
        width: 100%;
        margin-bottom: 1;
    }

    .selector-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
    }

    .selector-actions Button {
        margin: 0 1;
    }
    """

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

    DEFAULT_CSS = """
    KeyManager {
        width: 90;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    KeyManager.overlay {
        align: center middle;
        layer: overlay;
    }

    .manager-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .key-info {
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
        background: $surface-darken-1;
    }

    .key-status {
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    .manager-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
    }

    .manager-actions Button {
        margin: 0 1;
    }
    """

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
            yield Button("📦 Backup Key", variant="primary", id="backup-key-btn")
            yield Button("📥 Restore Key", variant="primary", id="restore-key-btn")
            yield Button("Close", variant="default", id="close-manager-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "regenerate-key-btn":
            self.regenerate_key()
        elif button_id == "show-key-path-btn":
            self.app.notify(f"Key path: {KEY_FILE}", severity="information")
        elif button_id == "backup-key-btn":
            self.backup_key()
        elif button_id == "restore-key-btn":
            self.restore_key()
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
    
    def backup_key(self) -> None:
        """Backup the encryption key to a user-specified location."""
        try:
            if not KEY_FILE.exists():
                self.app.notify("❌ No encryption key found to backup", severity="error")
                return
            
            # Create backup in home directory with timestamp
            from datetime import datetime
            backup_file = Path.home() / f"envcli_key_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.key"
            
            # Copy the key file
            import shutil
            shutil.copy2(KEY_FILE, backup_file)
            
            self.app.notify(f"✅ Key backed up to: {backup_file}", severity="success", timeout=8)
        except Exception as e:
            self.app.notify(f"❌ Failed to backup key: {e}", severity="error")
    
    def restore_key(self) -> None:
        """Restore encryption key from a backup file."""
        try:
            # Simple file dialog simulation - for now, use home directory
            home_dir = Path.home()
            backup_files = list(home_dir.glob("envcli_key_backup_*.key"))
            
            if not backup_files:
                self.app.notify("❌ No backup files found in home directory", severity="error")
                return
            
            # Use the most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            # Create a restore confirmation
            self.app.notify(f"🔄 Restoring key from: {latest_backup.name}", severity="information")
            
            # Check if current key exists and ask for confirmation
            if KEY_FILE.exists():
                self.app.notify("⚠️ Current key will be overwritten!", severity="warning")
            
            # Perform the restore
            import shutil
            shutil.copy2(latest_backup, KEY_FILE)
            
            self.app.notify("✅ Key restored successfully", severity="success")
            self.post_message(self.KeyRegenerated())
        except Exception as e:
            self.app.notify(f"❌ Failed to restore key: {e}", severity="error")


class EncryptionScreen(Container):
    """Main encryption screen."""

    DEFAULT_CSS = """
    EncryptionScreen {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    .screen-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        height: 3;
        content-align: center middle;
    }

    .stats-bar {
        height: 3;
        background: $surface;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    .action-bar {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }

    .action-bar Button {
        margin-right: 1;
    }

    .content-area {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }

    .encryption-info {
        height: 100%;
        overflow-y: auto;
    }

    .encryption-info-text {
        margin-bottom: 2;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
    }

    .file-status {
        margin-bottom: 1;
        padding-left: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
    
    def compose(self) -> ComposeResult:
        """Compose the encryption screen."""
        # Header
        yield Static("[ Encryption & Security", classes="screen-title")

        # Status bar with enhanced information
        status_text = Text()
        status_text.append("📁 Profile: ", style="#757575")
        status_text.append(self.current_profile, style="bold #00E676")
        status_text.append("  |  🔑 Key: ", style="#757575")

        if KEY_FILE.exists():
            key_size = KEY_FILE.stat().st_size
            status_text.append(f"+ Exists ({key_size} bytes)", style="bold #00E676")
        else:
            status_text.append("X Not Found", style="bold #FF5252")

        # Add profile encryption status
        profiles_dir = PROFILES_DIR
        if profiles_dir.exists():
            profile_files = list(profiles_dir.glob("*.json"))
            encrypted_count = sum(1 for f in profile_files if self._check_file_encryption_status(f) == "encrypted")
            total_count = len(profile_files)
            status_text.append(f"  |  📄 Files: {encrypted_count}/{total_count} Encrypted", style="#64FFDA")

        yield Static(status_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("[ Encrypt File", variant="success", id="encrypt-file-btn")
            yield Button("🔓 Decrypt File", variant="primary", id="decrypt-file-btn")
            yield Button("🔄 Batch Encrypt", variant="success", id="batch-encrypt-btn")
            yield Button("🔄 Batch Decrypt", variant="primary", id="batch-decrypt-btn")
            yield Button("🔑 Manage Key", variant="default", id="manage-key-btn")
            yield Button("= Check Status", variant="default", id="check-status-btn")
            yield Button("📊 Security Report", variant="default", id="security-report-btn")
        
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
        elif button_id == "batch-encrypt-btn":
            self.show_batch_encrypt()
        elif button_id == "batch-decrypt-btn":
            self.show_batch_decrypt()
        elif button_id == "security-report-btn":
            self.show_security_report()
    
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
            file_path_obj = Path(file_path)

            # Validate file exists
            if not file_path_obj.exists():
                self.app.notify(f"❌ File not found: {file_path}", severity="error", timeout=5)
                return

            # Validate file is readable
            if not file_path_obj.is_file():
                self.app.notify(f"❌ Path is not a file: {file_path}", severity="error", timeout=5)
                return

            if operation == "encrypt":
                self.app.notify(f"🔒 Encrypting {file_path_obj.name}...", severity="information")
                encrypt_file(file_path)
                self.app.notify(f"✅ Successfully encrypted {file_path_obj.name}", severity="information", timeout=5)
            else:
                self.app.notify(f"🔓 Decrypting {file_path_obj.name}...", severity="information")
                decrypt_file(file_path)
                self.app.notify(f"✅ Successfully decrypted {file_path_obj.name}", severity="information", timeout=5)

            # Refresh status display
            await self.refresh_status()
        except FileNotFoundError as e:
            self.app.notify(f"❌ File not found: {file_path}", severity="error", timeout=5)
        except ValueError as e:
            self.app.notify(f"❌ Decryption failed: {str(e)}", severity="error", timeout=8)
        except PermissionError as e:
            self.app.notify(f"❌ Permission denied: {file_path}", severity="error", timeout=5)
        except Exception as e:
            self.app.notify(f"❌ Operation failed: {str(e)}", severity="error", timeout=8)
    
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
    
    def show_batch_encrypt(self) -> None:
        """Show batch encryption interface."""
        self.run_worker(self._mount_batch_modal("encrypt"))
    
    def show_batch_decrypt(self) -> None:
        """Show batch decryption interface."""
        self.run_worker(self._mount_batch_modal("decrypt"))
    
    async def _mount_batch_modal(self, operation: str) -> None:
        """Mount the batch operation modal."""
        try:
            existing = self.query_one(BatchEncryptionModal)
            await existing.remove()
        except:
            pass
        
        modal = BatchEncryptionModal(operation)
        await self.mount(modal)
        modal.add_class("overlay")
    
    def show_security_report(self) -> None:
        """Show comprehensive security report."""
        self.run_worker(self._generate_security_report())
    
    async def _generate_security_report(self) -> None:
        """Generate and show security report."""
        try:
            # Analyze all profile files
            profiles_dir = PROFILES_DIR
            if not profiles_dir.exists():
                self.app.notify("❌ No profiles directory found", severity="error")
                return
            
            profile_files = list(profiles_dir.glob("*.json"))
            if not profile_files:
                self.app.notify("❌ No profile files found", severity="error")
                return
            
            # Gather security data
            total_files = len(profile_files)
            encrypted_files = 0
            plain_files = 0
            total_size = 0
            
            security_analysis = {
                "encryption_status": {},
                "file_sizes": {},
                "security_score": 0,
                "recommendations": []
            }
            
            for profile_file in profile_files:
                status = self._check_file_encryption_status(profile_file)
                file_size = profile_file.stat().st_size
                total_size += file_size
                
                security_analysis["encryption_status"][profile_file.name] = status
                security_analysis["file_sizes"][profile_file.name] = file_size
                
                if status == "encrypted":
                    encrypted_files += 1
                elif status == "plain":
                    plain_files += 1
            
            # Calculate security score
            if total_files > 0:
                security_score = (encrypted_files / total_files) * 100
                security_analysis["security_score"] = int(security_score)
            
            # Generate recommendations
            if plain_files > 0:
                security_analysis["recommendations"].append(f"🔒 Encrypt {plain_files} unencrypted profile files")
            
            if not KEY_FILE.exists():
                security_analysis["recommendations"].append("🔑 Create encryption key for secure storage")
            
            if total_size > 100000:  # 100KB
                security_analysis["recommendations"].append("💾 Consider encrypting large profile files")
            
            # Show report in a modal
            await self._mount_security_report_modal(security_analysis)
                
        except Exception as e:
            self.app.notify(f"❌ Security report failed: {e}", severity="error")
    
    async def _mount_security_report_modal(self, security_data: dict) -> None:
        """Mount the security report modal."""
        try:
            existing = self.query_one(SecurityReportModal)
            await existing.remove()
        except:
            pass
        
        modal = SecurityReportModal(security_data)
        await self.mount(modal)
        modal.add_class("overlay")
        
    async def _remove_batch_modal(self) -> None:
        """Remove the batch modal."""
        try:
            modal = self.query_one(BatchEncryptionModal)
            await modal.remove()
        except:
            pass

    async def _remove_security_modal(self) -> None:
        """Remove the security report modal."""
        try:
            modal = self.query_one(SecurityReportModal)
            await modal.remove()
        except:
            pass
    
    def on_security_report_modal_modal_closed(self, message) -> None:
        """Handle security report modal dismissed."""
        self.run_worker(self._remove_security_modal())
    
    def on_batch_encryption_modal_modal_closed(self, message) -> None:
        """Handle batch modal dismissed."""
        self.run_worker(self._remove_batch_modal())
        # Refresh status after batch operation
        self.run_worker(self.refresh_status())


class SecurityReportModal(Container):
    """Modal for displaying detailed security report."""

    DEFAULT_CSS = """
SecurityReportModal {
    width: 90;
        height: auto;
    max-height: 30;
background: $surface;
border: thick $primary;
        padding: 2;
    }

    SecurityReportModal.overlay {
        align: center middle;
        layer: overlay;
    }

    .modal-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .stats-bar {
        height: auto;
        background: $surface;
        border: solid $border;
        padding: 1;
        margin-bottom: 1;
    }

    .info-label {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
    }

    .modal-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    .modal-actions Button {
        margin: 0 1;
    }
    """

    class ModalClosed(Message):
        """Message sent when modal is closed."""

    def __init__(self, security_data: dict):
        super().__init__()
        self.security_data = security_data

    def compose(self) -> ComposeResult:
        """Compose the security report modal."""
        with Container():
            yield Static("🔒 Security Report", classes="modal-title")
            
            # Security score
            score = self.security_data.get("security_score", 0)
            score_text = Text()
            score_text.append("Security Score: ", style="#757575")
            if score >= 80:
                score_text.append(f"{score}% (Excellent)", style="bold #00E676")
            elif score >= 60:
                score_text.append(f"{score}% (Good)", style="bold #FFB300")
            else:
                score_text.append(f"{score}% (Needs Improvement)", style="bold #FF5252")
            
            yield Static(score_text, classes="stats-bar")
            
            # Detailed breakdown
            yield Static("📊 Detailed Breakdown", classes="info-label")
            
            encryption_status = self.security_data.get("encryption_status", {})
            for file_name, status in encryption_status.items():
                status_text = Text()
                status_text.append(f"• {file_name}: ", style="#E0E0E0")
                if status == "encrypted":
                    status_text.append("🔒 Encrypted", style="#00E676")
                elif status == "plain":
                    status_text.append("🔓 Plain Text", style="#FFB300")
                else:
                    status_text.append("❓ Unknown", style="#757575")
                yield Static(status_text)
            
            # Recommendations
            if self.security_data.get("recommendations"):
                yield Static("\n💡 Recommendations:", classes="info-label")
                for rec in self.security_data["recommendations"]:
                    yield Static(f"• {rec}")
            
            # Actions
            with Horizontal(classes="modal-actions"):
                yield Button("📤 Export Report", variant="primary", id="export-report-btn")
                yield Button("🔒 Auto Encrypt", variant="success", id="auto-encrypt-btn")
                yield Button("❌ Close", variant="default", id="close-report-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-report-btn":
            self.post_message(self.ModalClosed())
        elif button_id == "export-report-btn":
            self.export_report()
        elif button_id == "auto-encrypt-btn":
            self.auto_encrypt()

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

    def export_report(self) -> None:
        """Export the security report."""
        try:
            from datetime import datetime
            import json
            report_file = Path.home() / f"envcli_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(self.security_data, f, indent=2)
            
            self.app.notify(f"📤 Security report exported to: {report_file.name}", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Export failed: {e}", severity="error")

    def auto_encrypt(self) -> None:
        """Auto-encrypt all plain text files."""
        try:
            import shutil
            from pathlib import Path
            import time
            
            # Get all profile files that are in plain text
            profiles_dir = PROFILES_DIR  # Use the imported constant
            if not profiles_dir.exists():
                self.app.notify("❌ Profiles directory not found", severity="error")
                return
                
            plain_text_files = []
            for profile_file in profiles_dir.glob("*.json"):
                status = self._check_file_encryption_status(profile_file)
                if status == "plain":
                    plain_text_files.append(profile_file)
            
            if not plain_text_files:
                self.app.notify("✅ No plain text files to encrypt", severity="information")
                return
            
            # Create a backup before encryption
            backup_dir = profiles_dir / f"backup_{int(time.time())}"
            backup_dir.mkdir(exist_ok=True)
            
            for file_path in plain_text_files:
                # Create backup
                backup_path = backup_dir / f"{file_path.name}.backup"
                shutil.copy2(file_path, backup_path)
                
                # Encrypt the file
                from ...encryption import encrypt_file
                encrypt_file(str(file_path))
                
            self.app.notify(f"✅ Successfully encrypted {len(plain_text_files)} files", severity="success")
            self.post_message(self.ModalClosed())
            
        except Exception as e:
            self.app.notify(f"❌ Auto-encrypt failed: {e}", severity="error")


class BatchEncryptionModal(Container):
    """Modal for batch encryption/decryption operations."""

    DEFAULT_CSS = """
BatchEncryptionModal {
    width: 80;
        height: auto;
    max-height: 30;
background: $surface;
border: thick $primary;
padding: 2;
    }

    BatchEncryptionModal.overlay {
        align: center middle;
        layer: overlay;
    }

    .modal-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }

    .info-label {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
    }

    .modal-actions {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    .modal-actions Button {
        margin: 0 1;
    }

    .file-checkbox {
        width: 100%;
        margin-bottom: 1;
    }
    """

    class ModalClosed(Message):
        """Message sent when modal is closed."""

    def __init__(self, operation: str):
        super().__init__()
        self.operation = operation  # "encrypt" or "decrypt"
        self.profiles_dir = PROFILES_DIR

    def compose(self) -> ComposeResult:
        """Compose the batch operation modal."""
        title = "🔄 Batch Encrypt" if self.operation == "encrypt" else "🔄 Batch Decrypt"
        yield Static(title, classes="modal-title")
        
        # File selection
        yield Static("Select Files:", classes="info-label")
        
        self.selected_files = set()
        if self.profiles_dir.exists():
            for profile_file in sorted(self.profiles_dir.glob("*.json")):
                status = self._check_file_encryption_status(profile_file)
                should_include = (self.operation == "encrypt" and status == "plain") or \
                               (self.operation == "decrypt" and status == "encrypted")
                
                if should_include:
                    safe_id = profile_file.name.replace(".", "-")
                    checkbox = Button(
                        f"○ {profile_file.name}",
                        variant="default",
                        id=f"select-{safe_id}",
                        classes="file-checkbox"
                    )
                    yield checkbox
        
        # Options
        yield Static("\nOptions:", classes="info-label")
        yield Input(
            placeholder="Backup before operation (yes/no)",
            value="yes",
            id="backup-option-input"
        )
        
        # Actions
        with Horizontal(classes="modal-actions"):
            yield Button("🔄 Process Selected", variant="success", id="process-selected-btn")
            yield Button("🔄 Process All", variant="primary", id="process-all-btn")
            yield Button("❌ Cancel", variant="default", id="cancel-batch-btn")

    def _check_file_encryption_status(self, file_path: Path) -> str:
        """Check if a file is encrypted."""
        try:
            content = file_path.read_bytes()
            import json
            json.loads(content.decode('utf-8'))
            return "plain"
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "encrypted"
        except Exception:
            return "unknown"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-batch-btn":
            self.post_message(self.ModalClosed())
        elif button_id == "process-selected-btn":
            self.process_selected()
        elif button_id == "process-all-btn":
            self.process_all()
        elif button_id and button_id.startswith("select-"):
            file_name = button_id.replace("select-", "")
            file_name = file_name.replace("-", ".")
            self.toggle_file_selection(file_name)

    def toggle_file_selection(self, file_name: str) -> None:
        """Toggle file selection."""
        safe_id = file_name.replace(".", "-")
        if file_name in self.selected_files:
            self.selected_files.remove(file_name)
            button = self.query_one(f"#select-{safe_id}", Button)
            button.label = f"○ {file_name}"
            button.variant = "default"
        else:
            self.selected_files.add(file_name)
            button = self.query_one(f"#select-{safe_id}", Button)
            button.label = f"✓ {file_name}"
            button.variant = "success"

    def process_selected(self) -> None:
        """Process selected files."""
        if not self.selected_files:
            self.notify("Please select at least one file", severity="error")
            return
        
        self.run_worker(self._execute_batch_operation(list(self.selected_files)))

    def process_all(self) -> None:
        """Process all eligible files."""
        all_files = set()
        if self.profiles_dir.exists():
            for profile_file in self.profiles_dir.glob("*.json"):
                status = self._check_file_encryption_status(profile_file)
                should_include = (self.operation == "encrypt" and status == "plain") or \
                               (self.operation == "decrypt" and status == "encrypted")
                if should_include:
                    all_files.add(profile_file.name)
        
        if not all_files:
            action_text = "encrypt" if self.operation == "encrypt" else "decrypt"
            self.notify(f"No files to {action_text}", severity="error")
            return
        
        self.run_worker(self._execute_batch_operation(list(all_files)))

    async def _execute_batch_operation(self, files: list) -> None:
        """Execute the batch operation."""
        try:
            backup_option_input = self.query_one("#backup-option-input", Input)
            create_backup = backup_option_input.value.strip().lower() == "yes"
            
            action_text = "encrypt" if self.operation == "encrypt" else "decrypt"
            self.app.notify(f"🔄 {action_text.title()}ing {len(files)} files...", severity="information")
            
            success_count = 0
            failed_files = []
            
            for file_name in files:
                try:
                    file_path = self.profiles_dir / file_name
                    
                    # Create backup if requested
                    if create_backup:
                        backup_path = file_path.with_suffix(f".backup{file_path.suffix}")
                        import shutil
                        shutil.copy2(file_path, backup_path)
                    
                    # Perform operation
                    if self.operation == "encrypt":
                        encrypt_file(str(file_path))
                    else:
                        decrypt_file(str(file_path))
                    
                    success_count += 1
                except Exception as e:
                    failed_files.append(f"{file_name}: {str(e)}")
            
            # Show results
            if failed_files:
                failed_msg = f"⚠️ {success_count}/{len(files)} files processed. Failed: " + "; ".join(failed_files[:3])
                if len(failed_files) > 3:
                    failed_msg += f" (+{len(failed_files)-3} more)"
                self.app.notify(failed_msg, severity="warning")
            else:
                self.app.notify(f"✅ Successfully {action_text}ed {success_count} files", severity="success")

                self.post_message(self.ModalClosed())
            
        except Exception as e:
            self.app.notify(f"❌ Batch operation failed: {e}", severity="error")

