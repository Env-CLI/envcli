"""Profiles management screen for EnvCLI TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Input, DataTable, Label
from textual.message import Message
from textual.screen import ModalScreen
from rich.text import Text
from typing import Optional, List
from pathlib import Path
import os
import json
from datetime import datetime

from ...config import (
    list_profiles,
    create_profile,
    get_current_profile,
    set_current_profile,
    PROFILES_DIR
)
from ...env_manager import EnvManager


class ProfileCard(Container):
    """Enhanced card displaying comprehensive profile information."""

    def __init__(self, profile_name: str, is_active: bool = False):
        super().__init__()
        self.profile_name = profile_name
        self.is_active = is_active
        self.manager = EnvManager(profile_name)

        # Get enhanced profile metadata
        self.var_count = len(self.manager.load_env())
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        self.file_size = 0
        self.last_modified = "Unknown"
        self.created_date = "Unknown"
        self.sensitive_vars = 0
        self.total_size = 0

        if profile_file.exists():
            # File size in bytes
            self.file_size = profile_file.stat().st_size

            # Modification date
            mtime = profile_file.stat().st_mtime
            from datetime import datetime
            self.last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

            # Creation date (if available)
            try:
                ctime = profile_file.stat().st_ctime
                self.created_date = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d")
            except:
                pass

            # Calculate total content size and sensitive variables
            try:
                env_vars = self.manager.load_env()
                self.total_size = sum(len(str(v)) + len(str(k)) for k, v in env_vars.items())
                self.sensitive_vars = sum(1 for k in env_vars.keys()
                                        if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
            except:
                pass
    
    def compose(self) -> ComposeResult:
        """Compose the enhanced profile card."""
        # Card container with enhanced styling
        with Horizontal(classes="profile-card-main"):
            # Left side - Main info
            with Vertical(classes="profile-card-info"):
                # Card title with enhanced indicators
                title = Text()
                if self.is_active:
                    title.append("✓ ", style="bold #00E676")
                else:
                    title.append("○ ", style="bold #757575")
                title.append(self.profile_name,
                            style="bold #00E676" if self.is_active else "bold #64FFDA")
                yield Static(title, classes="profile-card-title")

                # Enhanced metadata
                meta = Text()
                meta.append(f"Variables: {self.var_count}", style="#00E676")
                if self.sensitive_vars > 0:
                    meta.append(f"  |  🔒 {self.sensitive_vars} sensitive", style="#FFB300")
                meta.append(f"\nModified: {self.last_modified}", style="#757575")
                meta.append(f"\nSize: {self.file_size} bytes", style="#757575")
                yield Static(meta, classes="profile-card-meta")

            # Right side - Action buttons - vertical layout for better space usage
            with Vertical(classes="profile-card-actions"):
                # First row of actions
                with Horizontal(classes="action-row"):
                    yield Button("📋 Details", variant="primary", id=f"details-{self.profile_name}")
                    if not self.is_active:
                        yield Button("🔄 Switch", variant="success", id=f"switch-{self.profile_name}")
                    else:
                        yield Button("⚡ Active", variant="success", disabled=True)

                # Second row of actions
                with Horizontal(classes="action-row"):
                    yield Button("📊 Compare", variant="default", id=f"compare-{self.profile_name}")
                    yield Button("📤 Export", variant="default", id=f"export-{self.profile_name}")
                    yield Button("🗑️ Delete", variant="error", id=f"delete-{self.profile_name}")


class ProfileCreator(Container):
    """Form for creating a new profile."""
    
    class ProfileCreated(Message):
        """Message sent when a profile is created."""
        def __init__(self, profile_name: str):
            self.profile_name = profile_name
            super().__init__()
    
    class CreatorClosed(Message):
        """Message sent when creator is closed."""
        pass
    
    def compose(self) -> ComposeResult:
        """Compose the creator form."""
        yield Static("Create New Profile", classes="creator-title")
        yield Label("Profile Name:")
        yield Input(placeholder="my-profile", id="profile-name-input")
        yield Label("Copy from existing profile (optional):")
        yield Input(placeholder="Leave empty for new profile", id="source-profile-input")
        with Horizontal():
            yield Button("Create", variant="success", id="create-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-btn":
            name_input = self.query_one("#profile-name-input", Input)
            source_input = self.query_one("#source-profile-input", Input)

            profile_name = name_input.value.strip()
            source_profile = source_input.value.strip()

            if not profile_name:
                self.app.notify("Profile name is required", severity="error")
                return

            # Check if profile already exists
            if profile_name in list_profiles():
                self.app.notify(f"Profile '{profile_name}' already exists", severity="error")
                return

            try:
                # Create the profile
                create_profile(profile_name)

                # Copy from source if specified
                if source_profile and source_profile in list_profiles():
                    source_manager = EnvManager(source_profile)
                    target_manager = EnvManager(profile_name)
                    env_vars = source_manager.load_env()
                    target_manager.save_env(env_vars)
                    self.app.notify(f"+ Created profile '{profile_name}' from '{source_profile}'", severity="information")
                else:
                    self.app.notify(f"+ Created empty profile '{profile_name}'", severity="information")

                self.post_message(self.ProfileCreated(profile_name))
            except Exception as e:
                self.app.notify(f"Failed to create profile: {e}", severity="error")
        elif event.button.id == "cancel-btn":
            self.post_message(self.CreatorClosed())


class ProfileComparison(Container):
    """Display comparison between two profiles."""
    
    def __init__(self, profile1: str, profile2: str):
        super().__init__()
        self.profile1 = profile1
        self.profile2 = profile2
        self.manager1 = EnvManager(profile1)
        self.manager2 = EnvManager(profile2)
    
    def compose(self) -> ComposeResult:
        """Compose the comparison view."""
        yield Static(f"Comparing: {self.profile1} ↔ {self.profile2}", classes="comparison-title")
        
        # Get diff
        diff = self.manager1.diff(self.profile2)
        
        # Added variables
        if diff["added"]:
            added_text = Text()
            added_text.append(f"+ Added in {self.profile2} ({len(diff['added'])})\n", style="bold #00E676")
            for key in diff["added"].keys():
                added_text.append(f"  • {key}\n", style="#00E676")
            yield Static(added_text, classes="diff-section")
        
        # Removed variables
        if diff["removed"]:
            removed_text = Text()
            removed_text.append(f"➖ Removed from {self.profile2} ({len(diff['removed'])})\n", style="bold #FF5252")
            for key in diff["removed"].keys():
                removed_text.append(f"  • {key}\n", style="#FF5252")
            yield Static(removed_text, classes="diff-section")
        
        # Changed variables
        if diff["changed"]:
            changed_text = Text()
            changed_text.append(f"@ Changed ({len(diff['changed'])})\n", style="bold #FFB300")
            for key in diff["changed"].keys():
                changed_text.append(f"  • {key}\n", style="#FFB300")
            yield Static(changed_text, classes="diff-section")
        
        # No differences
        if not diff["added"] and not diff["removed"] and not diff["changed"]:
            yield Static("+ Profiles are identical", classes="diff-section")
        
        yield Button("Close", variant="default", id="close-comparison-btn")


class ProfilesScreen(Container):
    """Comprehensive profiles management screen."""
    
    DEFAULT_CSS = """
    ProfilesScreen {
        height: 100%;
        overflow-y: auto;
    }

    ProfilesScreen .screen-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    ProfilesScreen .stats-bar {
        background: $surface;
        padding: 1 2;
        margin-bottom: 1;
    }

    ProfilesScreen .action-bar {
        margin-bottom: 1;
    }

    ProfilesScreen .action-bar Button {
        margin-right: 1;
    }

    ProfilesScreen .content-area {
        height: 1fr;
        overflow-y: auto;
    }

    ProfilesScreen .profile-list {
        height: 1fr;
        padding: 1 2;
    }

    ProfilesScreen ProfileCard {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    ProfilesScreen .profile-card-main {
        height: auto;
    }

    ProfilesScreen .profile-card-info {
        width: 70%;
    }

    ProfilesScreen .profile-card-actions {
        width: 35%;
        height: auto;
        align: center middle;
        padding: 1;
    }

    ProfilesScreen .action-row {
        height: auto;
        margin-bottom: 1;
        align: center middle;
    }

    ProfilesScreen .action-row Button {
        min-width: 12;
        height: 3;
        margin: 0 1;
    }

    ProfilesScreen .profile-card-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ProfilesScreen .profile-card-meta {
        margin-bottom: 1;
    }

    ProfilesScreen .quick-actions {
        background: $surface;
        padding: 1;
        margin-bottom: 1;
        border: solid $accent;
    }

    ProfilesScreen .quick-actions-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.show_creator = False
        self.show_comparison = False
        self.comparison_profile = None
        self.filter_text = ""
        self.view_mode = "cards"  # cards or table
    
    def compose(self) -> ComposeResult:
        """Compose the enhanced profiles screen."""
        # Header with enhanced title
        yield Static("🔧 Profile Management Center", classes="screen-title")
        
        # Enhanced stats bar with more information
        profiles = list_profiles()
        total_vars = sum(len(EnvManager(p).load_env()) for p in profiles)
        total_size = sum((PROFILES_DIR / f"{p}.json").stat().st_size
                        for p in profiles if (PROFILES_DIR / f"{p}.json").exists())
        
        stats_text = Text()
        stats_text.append(f"📊 Profiles: {len(profiles)}", style="bold #00E676")
        stats_text.append(f"  |  📦 Variables: {total_vars}", style="bold #64FFDA")
        stats_text.append(f"  |  💾 Storage: {total_size:,} bytes", style="bold #FFB300")
        stats_text.append(f"  |  ⚡ Active: {self.current_profile}", style="bold #00E676")
        yield Static(stats_text, classes="stats-bar")
        
        # Enhanced action bar
        with Horizontal(classes="action-bar"):
            yield Button("➕ Create Profile", variant="success", id="create-profile-btn")
            yield Button("🔄 Refresh", variant="default", id="refresh-profiles-btn")
            yield Button("📋 Table View", variant="default", id="table-view-btn")
            yield Button("🔍 Search", variant="default", id="search-profiles-btn")
            yield Button("🗂️ Batch Actions", variant="primary", id="batch-actions-btn")
        
        # Quick actions section
        with Vertical(classes="quick-actions"):
            yield Static("⚡ Quick Actions", classes="quick-actions-title")
            with Horizontal(classes="quick-actions-bar"):
                yield Button("📥 Import Profile", variant="default", id="quick-import-btn", classes="quick-action-btn")
                yield Button("📤 Export All", variant="default", id="quick-export-all-btn", classes="quick-action-btn")
                yield Button("🗑️ Clean Duplicates", variant="default", id="clean-duplicates-btn", classes="quick-action-btn")
                yield Button("📊 Analytics", variant="default", id="analytics-btn", classes="quick-action-btn")
        
        # Search bar (initially hidden)
        search_input = Input(placeholder="Search profiles by name...", id="profile-search-input", classes="search-input")
        search_input.display = False
        yield search_input
        
        # Main content area
        with Vertical(classes="content-area"):
            # Profile list (scrollable)
            with VerticalScroll(classes="profile-list"):
                yield from self._create_profile_list()
    
    def _create_profile_list(self, search_term: str = ""):
        """Yield profile cards with enhanced filtering."""
        profiles = list_profiles()

        # Filter profiles if search term provided
        if search_term:
            profiles = [p for p in profiles if search_term.lower() in p.lower()]

        self.app.log(f"Creating profile list with {len(profiles)} profiles: {profiles}")
        self.app.notify(f"Found {len(profiles)} profiles: {profiles}", severity="information")

        for profile in profiles:
            is_active = (profile == self.current_profile)
            self.app.log(f"Creating ProfileCard for {profile} (active={is_active})")
            yield ProfileCard(profile, is_active)

        self.app.notify(f"Yielded {len(profiles)} profile cards", severity="information")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses with enhanced functionality."""
        button_id = event.button.id

        # Log for debugging
        self.app.log(f"ProfilesScreen: Button pressed: {button_id}")

        if button_id == "create-profile-btn":
            self.show_profile_creator()
        elif button_id == "refresh-profiles-btn":
            self.app.notify("🔄 Refreshing profiles...", severity="information")
            self.run_worker(self.refresh_profiles())
        elif button_id == "table-view-btn":
            self.show_table_view()
        elif button_id == "search-profiles-btn":
            self.toggle_search()
        elif button_id == "batch-actions-btn":
            self.show_batch_actions()
        elif button_id == "quick-import-btn":
            self.quick_import()
        elif button_id == "quick-export-all-btn":
            self.quick_export_all()
        elif button_id == "clean-duplicates-btn":
            self.clean_duplicates()
        elif button_id == "analytics-btn":
            self.show_analytics()
        elif button_id and button_id.startswith("details-"):
            profile_name = button_id.replace("details-", "")
            self.show_profile_details(profile_name)
        elif button_id and button_id.startswith("switch-"):
            profile_name = button_id.replace("switch-", "")
            self.app.notify(f"🔄 Switching to profile: {profile_name}", severity="information")
            self.run_worker(self.switch_profile(profile_name))
        elif button_id and button_id.startswith("compare-"):
            profile_name = button_id.replace("compare-", "")
            self.show_comparison_view(profile_name)
        elif button_id and button_id.startswith("export-"):
            profile_name = button_id.replace("export-", "")
            self.show_export_dialog(profile_name)
        elif button_id and button_id.startswith("delete-"):
            profile_name = button_id.replace("delete-", "")
            self.confirm_delete_profile(profile_name)
        elif button_id == "close-comparison-btn":
            self.run_worker(self._remove_comparison())
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "profile-search-input":
            self.filter_text = event.value
            self.refresh_profiles()
    
    def toggle_search(self) -> None:
        """Toggle search input visibility."""
        search_input = self.query_one("#profile-search-input", Input)
        search_input.display = not search_input.display
        if search_input.display:
            search_input.focus()
        else:
            # Clear search when hiding
            search_input.value = ""
            self.filter_text = ""
            self.refresh_profiles()
    
    def show_profile_creator(self) -> None:
        """Show the profile creator form."""
        self.run_worker(self._mount_creator())

    async def _mount_creator(self) -> None:
        """Mount the enhanced profile creator form."""
        # Check if creator already exists
        try:
            existing = self.query_one(ProfileCreator)
            await existing.remove()
        except:
            pass

        # Mount new creator
        creator = ProfileCreator()
        await self.mount(creator)
        creator.add_class("overlay")

    def on_profile_creator_profile_created(self, message: ProfileCreator.ProfileCreated) -> None:
        """Handle profile created message."""
        # Remove the creator
        self.run_worker(self._remove_creator())
        # Refresh profiles
        self.run_worker(self.refresh_profiles())
        self.app.notify(f"✅ Created profile: {message.profile_name}", severity="success")

    def on_profile_creator_creator_closed(self, message: ProfileCreator.CreatorClosed) -> None:
        """Handle creator closed message."""
        self.run_worker(self._remove_creator())

    async def _remove_creator(self) -> None:
        """Remove the profile creator form."""
        try:
            creator = self.query_one(ProfileCreator)
            await creator.remove()
        except:
            pass
    
    async def refresh_profiles(self) -> None:
        """Refresh the profile list with enhanced metadata."""
        # Update stats bar
        profiles = list_profiles()
        total_vars = sum(len(EnvManager(p).load_env()) for p in profiles)
        total_size = sum((PROFILES_DIR / f"{p}.json").stat().st_size
                        for p in profiles if (PROFILES_DIR / f"{p}.json").exists())
        
        stats_text = Text()
        stats_text.append(f"📊 Profiles: {len(profiles)}", style="bold #00E676")
        stats_text.append(f"  |  📦 Variables: {total_vars}", style="bold #64FFDA")
        stats_text.append(f"  |  💾 Storage: {total_size:,} bytes", style="bold #FFB300")
        stats_text.append(f"  |  ⚡ Active: {self.current_profile}", style="bold #00E676")

        try:
            stats_bar = self.query_one(".stats-bar", Static)
            stats_bar.update(stats_text)
        except:
            pass

        # Remove old list
        try:
            old_list = self.query_one(".profile-list", VerticalScroll)
            await old_list.remove()
        except:
            pass

        # Create new list with profile cards
        content_area = self.query_one(".content-area", Vertical)
        new_list = VerticalScroll(classes="profile-list")
        await content_area.mount(new_list)

        # Mount profile cards
        for profile in profiles:
            is_active = (profile == self.current_profile)
            await new_list.mount(ProfileCard(profile, is_active))
        
        # Update current profile
        self.current_profile = get_current_profile()
    
    def show_table_view(self) -> None:
        """Show all profiles in an enhanced table view."""
        self.app.push_screen(ProfileTableModal())
    
    def show_batch_actions(self) -> None:
        """Show batch actions modal."""
        self.app.push_screen(ProfileBatchActionsModal())
    
    def quick_import(self) -> None:
        """Quick import functionality."""
        self.app.push_screen(ProfileImportModal())
    
    def quick_export_all(self) -> None:
        """Quick export all profiles."""
        try:
            profiles = list_profiles()
            export_data = {}
            for profile in profiles:
                manager = EnvManager(profile)
                export_data[profile] = manager.load_env()
            
            export_file = Path.home() / "envcli_all_profiles_export.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.app.notify(f"✅ Exported {len(profiles)} profiles to {export_file}", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Export failed: {e}", severity="error")
    
    def clean_duplicates(self) -> None:
        """Clean up duplicate or invalid profiles."""
        self.app.push_screen(ProfileCleanModal())
    
    def show_analytics(self) -> None:
        """Show profile analytics."""
        self.app.push_screen(ProfileAnalyticsModal())
    
    def show_profile_details(self, profile_name: str) -> None:
        """Show detailed profile information."""
        self.app.push_screen(ProfileDetailsModal(profile_name))
    
    def show_comparison_view(self, profile_name: str) -> None:
        """Show comparison between current and selected profile."""
        self.comparison_profile = profile_name
        self.run_worker(self._mount_comparison(profile_name))

    async def _mount_comparison(self, profile_name: str) -> None:
        """Mount the enhanced profile comparison view."""
        # Check if comparison already exists
        try:
            existing = self.query_one(ProfileComparison)
            await existing.remove()
        except:
            pass

        # Mount new comparison
        comparison = ProfileComparison(self.current_profile, profile_name)
        await self.mount(comparison)
        comparison.add_class("overlay")

    async def _remove_comparison(self) -> None:
        """Remove the profile comparison view."""
        try:
            comparison = self.query_one(ProfileComparison)
            await comparison.remove()
        except:
            pass
    
    def show_export_dialog(self, profile_name: str) -> None:
        """Show export dialog for specific profile."""
        self.app.push_screen(ProfileExportModal(profile_name))
    
    def confirm_delete_profile(self, profile_name: str) -> None:
        """Confirm and delete a profile."""
        if profile_name == self.current_profile:
            self.app.notify(f"❌ Cannot delete active profile: {profile_name}", severity="error")
            return
        
        # Simple confirmation
        if profile_name in list_profiles():
            self.run_worker(self.delete_profile(profile_name))
        else:
            self.app.notify(f"❌ Profile not found: {profile_name}", severity="error")
    
    async def switch_profile(self, profile_name: str) -> None:
        """Switch to a different profile with enhanced feedback."""
        self.app.log(f"switch_profile called for: {profile_name}")

        # Update config
        set_current_profile(profile_name)
        self.current_profile = profile_name
        self.app.log(f"Updated current_profile to: {self.current_profile}")

        # Update the app's profile
        self.app.profile = profile_name
        self.app.log(f"Updated app.profile to: {self.app.profile}")

        # Update header
        try:
            from ..components.header import Header
            header = self.app.query_one(Header)
            header.update_profile(profile_name)
            self.app.log("Updated header")
        except Exception as e:
            self.app.log(f"Failed to update header: {e}")

        # Refresh the display
        self.app.log("Refreshing profiles display...")
        await self.refresh_profiles()

        # Show enhanced success message
        self.app.notify(f"✅ Switched to profile: {profile_name}", severity="success")
        self.app.log(f"Profile switch complete")
    
    async def delete_profile(self, profile_name: str) -> None:
        """Enhanced profile deletion with validation."""
        try:
            # Validate profile exists
            if profile_name not in list_profiles():
                self.app.notify(f"❌ Profile not found: {profile_name}", severity="error")
                return
            
            # Delete using proper config function if available
            if hasattr(self, '_delete_profile_safe'):
                await self._delete_profile_safe(profile_name)
            else:
                # Fallback deletion
                profile_file = PROFILES_DIR / f"{profile_name}.json"
                if profile_file.exists():
                    profile_file.unlink()
                    self.app.notify(f"✅ Deleted profile: {profile_name}", severity="success")
        except Exception as e:
            self.app.notify(f"❌ Failed to delete profile: {e}", severity="error")

        # Refresh the display
        await self.refresh_profiles()


class ProfileDetailsModal(ModalScreen):
    """Comprehensive profile details modal."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, profile_name: str):
        super().__init__()
        self.profile_name = profile_name
        self.manager = EnvManager(profile_name)
        
        # Get comprehensive profile information
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        self.var_count = len(self.manager.load_env())
        self.sensitive_vars = 0
        self.file_size = 0
        self.created_date = "Unknown"
        self.modified_date = "Unknown"
        
        try:
            env_vars = self.manager.load_env()
            self.sensitive_vars = sum(1 for k in env_vars.keys()
                                    if any(word in k.lower() for word in ['secret', 'key', 'token', 'password']))
        except:
            pass
        
        if profile_file.exists():
            self.file_size = profile_file.stat().st_size
            try:
                from datetime import datetime
                ctime = profile_file.stat().st_ctime
                mtime = profile_file.stat().st_mtime
                self.created_date = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
                self.modified_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            except:
                pass

    def compose(self) -> ComposeResult:
        """Compose the profile details modal."""
        with Container():
            yield Static(f"📋 Profile Details: {self.profile_name}", classes="modal-title")
            
            # Profile information grid
            with Vertical(classes="profile-info"):
                yield Static("📊 Profile Information", classes="info-label")
                with Vertical(classes="info-grid"):
                    yield Static(f"Variables Count: {self.var_count}", classes="info-value")
                    yield Static(f"Sensitive Variables: {self.sensitive_vars}", classes="info-value")
                    yield Static(f"File Size: {self.file_size:,} bytes", classes="info-value")
                    yield Static(f"Created: {self.created_date}", classes="info-value")
                    yield Static(f"Modified: {self.modified_date}", classes="info-value")
            
            # Variables table
            yield Static("📦 Variables", classes="info-label")
            table = DataTable(id="profile-vars-table")
            table.add_columns("Variable", "Value Preview", "Type")
            
            try:
                env_vars = self.manager.load_env()
                for key, value in sorted(env_vars.items()):
                    # Determine variable type
                    var_type = "🔓 Regular"
                    if any(word in key.lower() for word in ['secret', 'key', 'token', 'password']):
                        var_type = "🔒 Sensitive"
                    
                    # Value preview (truncate if too long)
                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    table.add_row(key, value_preview, var_type)
            except Exception as e:
                yield Static(f"Error loading variables: {e}", classes="info-value")
            
            yield table
            
            # Action buttons
            with Horizontal(classes="modal-actions"):
                yield Button("📤 Export", variant="primary", id="export-profile-btn")
                yield Button("🔄 Switch To", variant="success", id="switch-to-profile-btn")
                yield Button("🗑️ Delete", variant="error", id="delete-profile-btn")
                yield Button("❌ Close", variant="default", id="close-details-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-details-btn":
            self.dismiss()
        elif button_id == "export-profile-btn":
            self.export_profile()
        elif button_id == "switch-to-profile-btn":
            self.switch_to_profile()
        elif button_id == "delete-profile-btn":
            self.delete_profile()

    def export_profile(self) -> None:
        """Export this profile."""
        try:
            env_vars = self.manager.load_env()
            export_file = Path.home() / f"envcli_{self.profile_name}_export.json"
            with open(export_file, 'w') as f:
                json.dump(env_vars, f, indent=2)
            
            self.notify(f"✅ Exported profile to {export_file}", severity="success")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    def switch_to_profile(self) -> None:
        """Switch to this profile."""
        # Send message to parent to switch
        from ...config import set_current_profile
        set_current_profile(self.profile_name)
        self.dismiss()
        
        # Notify user
        self.notify(f"✅ Switched to profile: {self.profile_name}", severity="success")

    def delete_profile(self) -> None:
        """Delete this profile."""
        if self.profile_name == get_current_profile():
            self.notify("❌ Cannot delete active profile", severity="error")
            return
        
        try:
            profile_file = PROFILES_DIR / f"{self.profile_name}.json"
            if profile_file.exists():
                profile_file.unlink()
                self.notify(f"✅ Deleted profile: {self.profile_name}", severity="success")
                self.dismiss()
        except Exception as e:
            self.notify(f"❌ Delete failed: {e}", severity="error")


class ProfileExportModal(ModalScreen):
    """Export profile modal with multiple format options."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, profile_name: str):
        super().__init__()
        self.profile_name = profile_name
        self.manager = EnvManager(profile_name)

    def compose(self) -> ComposeResult:
        """Compose the export modal."""
        with Container():
            yield Static(f"📤 Export Profile: {self.profile_name}", classes="modal-title")
            
            yield Label("Export location:")
            yield Input(
                placeholder=f"/path/to/{self.profile_name}_export.json",
                id="export-location-input"
            )
            
            yield Label("Export format:")
            yield Input(
                placeholder="json, yaml, env, or envcli",
                value="json",
                id="export-format-input"
            )
            
            yield Label("Export options:")
            yield Input(
                placeholder="mask (hide sensitive) or show (include all)",
                value="mask",
                id="export-options-input"
            )
            
            with Horizontal(classes="modal-actions"):
                yield Button("📤 Export", variant="success", id="confirm-export-btn")
                yield Button("❌ Cancel", variant="default", id="cancel-export-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "confirm-export-btn":
            self.perform_export()
        elif button_id == "cancel-export-btn":
            self.dismiss()

    def perform_export(self) -> None:
        """Perform the export with specified options."""
        try:
            location_input = self.query_one("#export-location-input", Input)
            format_input = self.query_one("#export-format-input", Input)
            options_input = self.query_one("#export-options-input", Input)
            
            export_path = location_input.value.strip()
            export_format = format_input.value.strip().lower() or "json"
            export_options = options_input.value.strip().lower() or "mask"
            
            if not export_path:
                self.notify("Please specify export location", severity="error")
                return
            
            # Get variables to export
            if export_options == "show":
                variables = self.manager.load_env()
            else:  # mask
                variables = self.manager.list_env(mask=True)
            
            # Ensure directory exists
            path = Path(export_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
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
                    self.notify("PyYAML not installed - cannot export to YAML", severity="error")
                    return
            elif export_format == "env":
                with open(path, 'w') as f:
                    f.write(f"# Environment variables for {self.profile_name}\n")
                    f.write(f"# Generated by EnvCLI\n\n")
                    for key, value in sorted(variables.items()):
                        f.write(f"{key}={value}\n")
            else:  # envcli format
                export_data = {
                    "profile": self.profile_name,
                    "variables": variables,
                    "exported_at": datetime.now().isoformat(),
                    "format": "envcli"
                }
                with open(path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            # Verify export
            if path.exists():
                file_size = path.stat().st_size
                self.notify(f"✅ Exported {len(variables)} variables to {export_path} ({file_size} bytes)", severity="success")
                self.dismiss()
            else:
                self.notify("❌ Export failed - file not created", severity="error")
                
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")


class ProfileTableModal(ModalScreen):
    """Comprehensive table view of all profiles."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.profiles_data = self._gather_profiles_data()

    def _gather_profiles_data(self) -> List[dict]:
        """Gather comprehensive data for all profiles."""
        profiles = list_profiles()
        data = []
        
        for profile in profiles:
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                profile_file = PROFILES_DIR / f"{profile}.json"
                
                profile_data = {
                    "name": profile,
                    "active": profile == get_current_profile(),
                    "var_count": len(env_vars),
                    "sensitive_count": sum(1 for k in env_vars.keys()
                                         if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])),
                    "file_size": profile_file.stat().st_size if profile_file.exists() else 0,
                    "created": "Unknown",
                    "modified": "Unknown"
                }
                
                if profile_file.exists():
                    try:
                        from datetime import datetime
                        ctime = profile_file.stat().st_ctime
                        mtime = profile_file.stat().st_mtime
                        profile_data["created"] = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d")
                        profile_data["modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                    except:
                        pass
                
                data.append(profile_data)
            except Exception as e:
                # Add minimal data for profiles that can't be loaded
                data.append({
                    "name": profile,
                    "active": profile == get_current_profile(),
                    "var_count": 0,
                    "sensitive_count": 0,
                    "file_size": 0,
                    "created": "Error",
                    "modified": "Error"
                })
        
        return data

    def compose(self) -> ComposeResult:
        """Compose the table view modal."""
        with Container():
            yield Static("📊 All Profiles Overview", classes="modal-title")
            
            # Summary statistics
            total_profiles = len(self.profiles_data)
            total_vars = sum(p["var_count"] for p in self.profiles_data)
            total_size = sum(p["file_size"] for p in self.profiles_data)
            active_profiles = sum(1 for p in self.profiles_data if p["active"])
            
            summary = Text()
            summary.append(f"Total Profiles: {total_profiles}  ", style="bold #00E676")
            summary.append(f"Total Variables: {total_vars}  ", style="bold #64FFDA")
            summary.append(f"Storage: {total_size:,} bytes  ", style="bold #FFB300")
            summary.append(f"Active: {active_profiles}", style="bold #00E676")
            
            yield Static(summary, classes="stats-bar")
            
            # Table
            table = DataTable(id="profiles-table")
            table.add_columns("Profile", "Variables", "Sensitive", "Size (bytes)", "Created", "Modified", "Actions")
            
            # Sort by name
            sorted_profiles = sorted(self.profiles_data, key=lambda x: x["name"].lower())
            
            for profile in sorted_profiles:
                status = "⚡ Active" if profile["active"] else "○ Inactive"
                actions = "Switch" if not profile["active"] else "Details"
                table.add_row(
                    f"{profile['name']} {status}",
                    str(profile["var_count"]),
                    str(profile["sensitive_count"]),
                    str(profile["file_size"]),
                    profile["created"],
                    profile["modified"],
                    actions
                )
            
            yield table
            
            # Action buttons
            with Horizontal(classes="modal-actions"):
                yield Button("📊 Analytics", variant="primary", id="table-analytics-btn")
                yield Button("📤 Export Table", variant="default", id="export-table-btn")
                yield Button("🗂️ Batch Actions", variant="default", id="batch-table-btn")
                yield Button("❌ Close", variant="default", id="close-table-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-table-btn":
            self.dismiss()
        elif button_id == "table-analytics-btn":
            self.show_table_analytics()
        elif button_id == "export-table-btn":
            self.export_table()
        elif button_id == "batch-table-btn":
            self.show_batch_actions()
        elif button_id.startswith("row-"):
            # Handle row actions
            row_data = button_id.split("-", 2)
            if len(row_data) >= 3:
                action = row_data[1]
                profile_name = row_data[2]
                self.handle_row_action(action, profile_name)

    def show_table_analytics(self) -> None:
        """Show analytics for the table view."""
        # Create analytics data similar to ProfileAnalyticsModal
        analytics_data = TableAnalyticsModal._generate_table_analytics_static()

        # Show in a modal
        self.app.push_screen(TableAnalyticsModal(analytics_data))

    def export_table(self) -> None:
        """Export the table data."""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_profiles": len(self.profiles_data),
                "profiles": self.profiles_data
            }
            
            export_file = Path.home() / "envcli_profiles_table_export.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.notify(f"✅ Exported table to {export_file}", severity="success")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    def show_batch_actions(self) -> None:
        """Show batch actions for profiles."""
        self.app.push_screen(ProfileBatchActionsModal())

    def handle_row_action(self, action: str, profile_name: str):
        """Handle actions from table rows."""
        if action == "switch":
            from ...config import set_current_profile
            set_current_profile(profile_name)
            self.notify(f"✅ Switched to profile: {profile_name}", severity="success")
            self.dismiss()
        elif action == "details":
            self.app.push_screen(ProfileDetailsModal(profile_name))


class ProfileImportModal(ModalScreen):
    """Import profiles modal with multiple format support."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the import modal."""
        with Container():
            yield Static("📥 Import Profiles", classes="modal-title")
            
            yield Label("Import location:")
            yield Input(
                placeholder="/path/to/profiles_import.json",
                id="import-location-input"
            )
            
            yield Label("Import format:")
            yield Input(
                placeholder="json, yaml, env, or envcli",
                value="json",
                id="import-format-input"
            )
            
            yield Label("Profile name prefix (optional):")
            yield Input(
                placeholder="e.g., imported_",
                id="import-prefix-input"
            )
            
            yield Label("Merge strategy:")
            yield Input(
                placeholder="merge (combine) or replace (overwrite)",
                value="merge",
                id="import-strategy-input"
            )
            
            with Horizontal(classes="modal-actions"):
                yield Button("📥 Import", variant="success", id="confirm-import-btn")
                yield Button("❌ Cancel", variant="default", id="cancel-import-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "confirm-import-btn":
            self.perform_import()
        elif button_id == "cancel-import-btn":
            self.dismiss()

    def perform_import(self) -> None:
        """Perform the import with specified options."""
        try:
            location_input = self.query_one("#import-location-input", Input)
            format_input = self.query_one("#import-format-input", Input)
            prefix_input = self.query_one("#import-prefix-input", Input)
            strategy_input = self.query_one("#import-strategy-input", Input)
            
            import_path = location_input.value.strip()
            import_format = format_input.value.strip().lower() or "json"
            prefix = prefix_input.value.strip()
            strategy = strategy_input.value.strip().lower() or "merge"
            
            if not import_path:
                self.notify("Please specify import location", severity="error")
                return
            
            # Check if file exists
            path = Path(import_path)
            if not path.exists():
                self.notify(f"❌ File not found: {import_path}", severity="error")
                return
            
            imported_count = 0
            
            # Import based on format
            if import_format == "json":
                with open(path, 'r') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, dict):
                        if 'profile' in data and 'variables' in data:
                            # Single envcli format
                            profile_name = prefix + data['profile']
                            self._import_profile_data(profile_name, data['variables'], strategy)
                            imported_count = 1
                        else:
                            # Multiple profiles format
                            for profile_name, variables in data.items():
                                if isinstance(variables, dict):
                                    import_name = prefix + profile_name
                                    self._import_profile_data(import_name, variables, strategy)
                                    imported_count += 1
                    else:
                        self.notify("❌ Invalid JSON format", severity="error")
                        return
            
            elif import_format == "yaml":
                try:
                    import yaml
                    with open(path, 'r') as f:
                        data = yaml.safe_load(f)
                        if isinstance(data, dict):
                            for profile_name, variables in data.items():
                                if isinstance(variables, dict):
                                    import_name = prefix + profile_name
                                    self._import_profile_data(import_name, variables, strategy)
                                    imported_count += 1
                        else:
                            self.notify("❌ Invalid YAML format", severity="error")
                            return
                except ImportError:
                    self.notify("❌ PyYAML not installed - cannot import YAML", severity="error")
                    return
            
            elif import_format == "env":
                # Import .env file as single profile
                profile_name = prefix + path.stem
                variables = self._parse_env_file(path)
                if variables:
                    self._import_profile_data(profile_name, variables, strategy)
                    imported_count = 1
                else:
                    self.notify("❌ No variables found in .env file", severity="error")
                    return
            else:
                self.notify("❌ Unsupported import format", severity="error")
                return
            
            # Success notification
            if imported_count > 0:
                self.notify(f"✅ Imported {imported_count} profiles from {import_path}", severity="success")
                self.dismiss()
            else:
                self.notify("❌ No profiles were imported", severity="error")
                
        except Exception as e:
            self.notify(f"❌ Import failed: {e}", severity="error")

    def _import_profile_data(self, profile_name: str, variables: dict, strategy: str) -> None:
        """Import profile data with specified strategy."""
        try:
            from ...config import create_profile
            
            # Check if profile exists
            existing_profiles = list_profiles()
            
            if profile_name in existing_profiles and strategy == "replace":
                # Replace existing profile
                manager = EnvManager(profile_name)
                manager.save_env(variables)
            elif profile_name not in existing_profiles:
                # Create new profile
                create_profile(profile_name)
                manager = EnvManager(profile_name)
                manager.save_env(variables)
            elif strategy == "merge":
                # Merge with existing
                manager = EnvManager(profile_name)
                existing_vars = manager.load_env()
                existing_vars.update(variables)
                manager.save_env(existing_vars)
            # If strategy is merge but profile doesn't exist, it's handled above
            
        except Exception as e:
            self.notify(f"❌ Failed to import profile {profile_name}: {e}", severity="error")

    def _parse_env_file(self, path: Path) -> dict:
        """Parse .env file and return variables dictionary."""
        variables = {}
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        variables[key.strip()] = value
        except Exception as e:
            self.notify(f"❌ Error parsing .env file: {e}", severity="error")
            return {}
        return variables


class ProfileCleanModal(ModalScreen):
    """Clean up duplicate or invalid profiles."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.issues = self._analyze_problems()

    def _analyze_problems(self) -> List[dict]:
        """Analyze profiles for potential issues."""
        profiles = list_profiles()
        issues = []
        
        for profile in profiles:
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                profile_file = PROFILES_DIR / f"{profile}.json"
                
                # Check for empty profiles
                if not env_vars:
                    issues.append({
                        "profile": profile,
                        "type": "empty",
                        "description": "Profile has no variables",
                        "severity": "warning"
                    })
                
                # Check for duplicate variables within profile
                var_names = list(env_vars.keys())
                if len(var_names) != len(set(var_names)):
                    issues.append({
                        "profile": profile,
                        "type": "duplicate_vars",
                        "description": "Profile has duplicate variable names",
                        "severity": "error"
                    })
                
                # Check for suspicious variable names
                suspicious_vars = [var for var in var_names if var.startswith('_') and len(var) < 3]
                if suspicious_vars:
                    issues.append({
                        "profile": profile,
                        "type": "suspicious_vars",
                        "description": f"Profile has suspicious variables: {', '.join(suspicious_vars)}",
                        "severity": "info"
                    })
                
            except Exception as e:
                issues.append({
                    "profile": profile,
                    "type": "corrupted",
                    "description": f"Profile is corrupted: {e}",
                    "severity": "error"
                })
        
        return issues

    def compose(self) -> ComposeResult:
        """Compose the clean modal."""
        with Container():
            yield Static("🧹 Profile Cleanup", classes="modal-title")
            
            if not self.issues:
                yield Static("✅ No issues found - all profiles look healthy!", classes="modal-title")
            else:
                # Issues summary
                error_count = sum(1 for issue in self.issues if issue["severity"] == "error")
                warning_count = sum(1 for issue in self.issues if issue["severity"] == "warning")
                info_count = sum(1 for issue in self.issues if issue["severity"] == "info")
                
                summary = Text()
                summary.append(f"Found {len(self.issues)} issues: ", style="bold")
                summary.append(f"{error_count} errors", style="bold #FF5252")
                summary.append(", ", style="#757575")
                summary.append(f"{warning_count} warnings", style="bold #FFB300")
                summary.append(", ", style="#757575")
                summary.append(f"{info_count} info", style="bold #64FFDA")
                
                yield Static(summary, classes="stats-bar")
                
                # Issues list
                yield Static("📋 Issues Found:", classes="info-label")
                
                for issue in self.issues:
                    icon = "❌" if issue["severity"] == "error" else "⚠️" if issue["severity"] == "warning" else "ℹ️"
                    color = "#FF5252" if issue["severity"] == "error" else "#FFB300" if issue["severity"] == "warning" else "#64FFDA"
                    
                    issue_text = Text()
                    issue_text.append(f"{icon} ", style=color)
                    issue_text.append(f"{issue['profile']}: ", style="bold #E0E0E0")
                    issue_text.append(issue['description'], style=color)
                    
                    yield Static(issue_text)
            
            # Action buttons
            with Horizontal(classes="modal-actions"):
                if self.issues:
                    yield Button("🧹 Auto Clean", variant="success", id="auto-clean-btn")
                    yield Button("⚙️ Manual Review", variant="primary", id="manual-review-btn")
                yield Button("❌ Close", variant="default", id="close-clean-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-clean-btn":
            self.dismiss()
        elif button_id == "auto-clean-btn":
            self.run_worker(self.perform_auto_clean())
        elif button_id == "manual-review-btn":
            self.show_manual_review()

    async def perform_auto_clean(self) -> None:
        """Perform automatic cleanup of issues."""
        cleaned_count = 0
        errors = []
        
        try:
            for issue in self.issues:
                try:
                    if issue["type"] == "empty":
                        # Remove empty profiles (but not active ones)
                        profile = issue["profile"]
                        if profile != get_current_profile():
                            profile_file = PROFILES_DIR / f"{profile}.json"
                            if profile_file.exists():
                                profile_file.unlink()
                                cleaned_count += 1
                                self.notify(f"✅ Removed empty profile: {profile}", severity="information")
                    
                    elif issue["type"] == "duplicate_vars":
                        # Remove duplicates from profile
                        manager = EnvManager(issue["profile"])
                        env_vars = manager.load_env()
                        unique_vars = dict.fromkeys(env_vars)  # Removes duplicates while preserving order
                        if len(unique_vars) < len(env_vars):
                            manager.save_env(unique_vars)
                            cleaned_count += 1
                            self.notify(f"✅ Cleaned duplicates in: {issue['profile']}", severity="information")
                            
                except Exception as e:
                    errors.append(f"{issue['profile']}: {e}")
            
            # Show results
            if errors:
                error_msg = f"⚠️ Cleaned {cleaned_count} issues, but {len(errors)} failed: " + "; ".join(errors[:3])
                if len(errors) > 3:
                    error_msg += f" (+{len(errors)-3} more)"
                self.notify(error_msg, severity="warning")
            else:
                self.notify(f"✅ Successfully cleaned {cleaned_count} issues", severity="success")
            
            self.dismiss()
            
        except Exception as e:
            self.notify(f"❌ Cleanup failed: {e}", severity="error")

    def show_manual_review(self) -> None:
        """Show manual review interface."""
        self.notify("📋 Manual Review - Feature coming soon!", severity="information")


class ProfileAnalyticsModal(ModalScreen):
    """Profile analytics and insights modal."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.analytics_data = self._generate_analytics()

    def _generate_analytics(self) -> dict:
        """Generate comprehensive analytics data."""
        profiles = list_profiles()
        data = {
            "total_profiles": len(profiles),
            "total_variables": 0,
            "total_size": 0,
            "profile_breakdown": [],
            "variable_types": {},
            "size_distribution": {},
            "active_profile": get_current_profile(),
            "recommendations": []
        }
        
        for profile in profiles:
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                profile_file = PROFILES_DIR / f"{profile}.json"
                
                profile_size = profile_file.stat().st_size if profile_file.exists() else 0
                
                profile_data = {
                    "name": profile,
                    "variables": len(env_vars),
                    "size": profile_size,
                    "sensitive_count": sum(1 for k in env_vars.keys()
                                         if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])),
                    "active": profile == data["active_profile"]
                }
                
                data["profile_breakdown"].append(profile_data)
                data["total_variables"] += len(env_vars)
                data["total_size"] += profile_size
                
                # Variable type analysis
                for var_name in env_vars.keys():
                    var_type = self._classify_variable(var_name)
                    data["variable_types"][var_type] = data["variable_types"].get(var_type, 0) + 1
                
            except Exception as e:
                data["recommendations"].append(f"⚠️ Failed to analyze {profile}: {e}")
        
        # Sort profiles by size
        data["profile_breakdown"].sort(key=lambda x: x["size"], reverse=True)
        
        # Generate recommendations
        self._generate_recommendations(data)
        
        return data

    def _classify_variable(self, var_name: str) -> str:
        """Classify variable based on naming patterns."""
        var_lower = var_name.lower()
        
        if any(word in var_lower for word in ['secret', 'key', 'token', 'password', 'auth']):
            return "Authentication"
        elif any(word in var_lower for word in ['db', 'database', 'sql']):
            return "Database"
        elif any(word in var_lower for word in ['api', 'url', 'endpoint']):
            return "API"
        elif any(word in var_lower for word in ['redis', 'cache']):
            return "Cache"
        elif any(word in var_lower for word in ['log', 'debug']):
            return "Logging"
        elif any(word in var_lower for word in ['port', 'host', 'server']):
            return "Network"
        else:
            return "General"

    def _generate_recommendations(self, data: dict) -> None:
        """Generate actionable recommendations."""
        # Check for large profiles
        large_profiles = [p for p in data["profile_breakdown"] if p["size"] > 10000]
        if large_profiles:
            data["recommendations"].append(f"💡 Consider optimizing {len(large_profiles)} large profiles (>10KB)")
        
        # Check for profiles with many variables
        heavy_profiles = [p for p in data["profile_breakdown"] if p["variables"] > 50]
        if heavy_profiles:
            data["recommendations"].append(f"💡 Consider splitting {len(heavy_profiles)} profiles with many variables (>50)")
        
        # Check for low variable profiles
        empty_profiles = [p for p in data["profile_breakdown"] if p["variables"] < 5]
        if empty_profiles:
            data["recommendations"].append(f"💡 Consider removing {len(empty_profiles)} very small profiles (<5 variables)")
        
        # Check sensitive variable distribution
        total_sensitive = sum(p["sensitive_count"] for p in data["profile_breakdown"])
        if total_sensitive > data["total_variables"] * 0.3:
            data["recommendations"].append("🔒 Consider using encryption for sensitive variables")
        
        # General recommendations
        if data["total_profiles"] > 10:
            data["recommendations"].append("📊 Consider organizing profiles by environment (dev, staging, prod)")
        
        if data["total_size"] > 100000:
            data["recommendations"].append("💾 Consider using external secret management for large datasets")

    def compose(self) -> ComposeResult:
        """Compose the analytics modal."""
        with Container():
            yield Static("📊 Profile Analytics & Insights", classes="modal-title")
            
            # Overview statistics
            overview = Text()
            overview.append(f"Total Profiles: {self.analytics_data['total_profiles']}  ", style="bold #00E676")
            overview.append(f"Total Variables: {self.analytics_data['total_variables']}  ", style="bold #64FFDA")
            overview.append(f"Total Size: {self.analytics_data['total_size']:,} bytes  ", style="bold #FFB300")
            overview.append(f"Active: {self.analytics_data['active_profile']}", style="bold #00E676")
            
            yield Static(overview, classes="stats-bar")
            
            # Top profiles by size
            yield Static("📈 Top Profiles by Size:", classes="info-label")
            for i, profile in enumerate(self.analytics_data["profile_breakdown"][:5]):
                profile_text = Text()
                status = "⚡ " if profile["active"] else "○ "
                profile_text.append(f"{i+1}. {status}{profile['name']} ", style="bold #E0E0E0")
                profile_text.append(f"({profile['variables']} vars, {profile['size']:,} bytes)", style="#757575")
                yield Static(profile_text)
            
            # Variable type distribution
            yield Static("🏷️ Variable Type Distribution:", classes="info-label")
            for var_type, count in sorted(self.analytics_data["variable_types"].items(),
                                         key=lambda x: x[1], reverse=True):
                percentage = (count / self.analytics_data["total_variables"]) * 100
                var_text = Text()
                var_text.append(f"• {var_type}: ", style="bold #64FFDA")
                var_text.append(f"{count} variables ({percentage:.1f}%)", style="#757575")
                yield Static(var_text)
            
            # Recommendations
            if self.analytics_data["recommendations"]:
                yield Static("💡 Recommendations:", classes="info-label")
                for recommendation in self.analytics_data["recommendations"]:
                    yield Static(f"• {recommendation}")
            else:
                yield Static("✅ All profiles look healthy!", classes="info-label")
            
            # Action buttons
            with Horizontal(classes="modal-actions"):
                yield Button("📊 Detailed Report", variant="primary", id="detailed-report-btn")
                yield Button("📤 Export Analytics", variant="default", id="export-analytics-btn")
                yield Button("❌ Close", variant="default", id="close-analytics-btn")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-analytics-btn":
            self.dismiss()
        elif button_id == "detailed-report-btn":
            self.show_detailed_report()
        elif button_id == "export-analytics-btn":
            self.export_analytics()

    def show_detailed_report(self) -> None:
        """Show detailed analytics report."""
        try:
            report_file = Path.home() / "envcli_analytics_report.json"
            with open(report_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2)
            
            self.notify(f"📊 Detailed report exported to {report_file}", severity="success")
        except Exception as e:
            self.notify(f"❌ Failed to export report: {e}", severity="error")

    def export_analytics(self) -> None:
        """Export analytics data."""
        try:
            analytics_file = Path.home() / "envcli_analytics_export.json"
            with open(analytics_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2)
            
            self.notify(f"📤 Analytics exported to {analytics_file}", severity="success")
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

class TableAnalyticsModal(ModalScreen):
    """Analytics modal for table view."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, analytics_data):
        super().__init__()
        self.analytics_data = analytics_data

    def compose(self) -> ComposeResult:
        """Compose the analytics modal."""
        with Container():
            yield Static("📊 Table View Analytics", classes="modal-title")

            # Overview statistics
            overview = Text()
            overview.append(f"Total Profiles: {self.analytics_data['total_profiles']}  ", style="bold #00E676")
            overview.append(f"Total Variables: {self.analytics_data['total_variables']}  ", style="bold #64FFDA")
            overview.append(f"Total Size: {self.analytics_data['total_size']:,} bytes", style="bold #FFB300")
            yield Static(overview, classes="stats-bar")

            # Profile breakdown
            yield Static("📈 Profile Breakdown:", classes="info-label")
            for profile in self.analytics_data["profile_breakdown"][:10]:  # Show top 10
                profile_text = Text()
                status = "⚡ " if profile["active"] else "○ "
                profile_text.append(f"{status}{profile['name']}: ", style="bold #E0E0E0")
                profile_text.append(f"{profile['variables']} vars, {profile['size']:,} bytes", style="#757575")
                if profile["sensitive_count"] > 0:
                    profile_text.append(f" (🔒 {profile['sensitive_count']} sensitive)", style="#FFB300")
                yield Static(profile_text)

            # Variable type distribution
            if self.analytics_data.get("variable_types"):
                yield Static("🏷️ Variable Types:", classes="info-label")
                for var_type, count in sorted(self.analytics_data["variable_types"].items(),
                                             key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / self.analytics_data["total_variables"]) * 100 if self.analytics_data["total_variables"] > 0 else 0
                    var_text = Text()
                    var_text.append(f"• {var_type}: ", style="bold #64FFDA")
                    var_text.append(f"{count} ({percentage:.1f}%)", style="#757575")
                    yield Static(var_text)

            # Recommendations
            if self.analytics_data.get("recommendations"):
                yield Static("💡 Recommendations:", classes="info-label")
                for recommendation in self.analytics_data["recommendations"][:3]:  # Show top 3
                    yield Static(f"• {recommendation}")

            yield Button("❌ Close", variant="default", id="close-analytics-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-analytics-btn":
            self.dismiss()

    @staticmethod
    def _generate_table_analytics_static() -> dict:
        """Generate analytics data for table view."""
        profiles = list_profiles()
        data = {
            "total_profiles": len(profiles),
            "total_variables": 0,
            "total_size": 0,
            "profile_breakdown": [],
            "variable_types": {},
            "recommendations": []
        }

        for profile in profiles:
            try:
                manager = EnvManager(profile)
                env_vars = manager.load_env()
                profile_file = PROFILES_DIR / f"{profile}.json"

                profile_size = profile_file.stat().st_size if profile_file.exists() else 0

                profile_data = {
                    "name": profile,
                    "variables": len(env_vars),
                    "size": profile_size,
                    "sensitive_count": sum(1 for k in env_vars.keys()
                                         if any(word in k.lower() for word in ['secret', 'key', 'token', 'password'])),
                    "active": profile == get_current_profile()
                }

                data["profile_breakdown"].append(profile_data)
                data["total_variables"] += len(env_vars)
                data["total_size"] += profile_size

                # Variable type analysis
                for var_name in env_vars.keys():
                    var_type = TableAnalyticsModal._classify_variable_for_table_static(var_name)
                    data["variable_types"][var_type] = data["variable_types"].get(var_type, 0) + 1

            except Exception as e:
                data["recommendations"].append(f"⚠️ Failed to analyze {profile}: {e}")

        # Sort profiles by size
        data["profile_breakdown"].sort(key=lambda x: x["size"], reverse=True)

        # Generate recommendations
        TableAnalyticsModal._generate_table_recommendations_static(data)

        return data

    @staticmethod
    def _classify_variable_for_table_static(var_name: str) -> str:
        """Classify variable for table analytics."""
        var_lower = var_name.lower()

        if any(word in var_lower for word in ['secret', 'key', 'token', 'password', 'auth']):
            return "Authentication"
        elif any(word in var_lower for word in ['db', 'database', 'sql']):
            return "Database"
        elif any(word in var_lower for word in ['api', 'url', 'endpoint']):
            return "API"
        elif any(word in var_lower for word in ['redis', 'cache']):
            return "Cache"
        elif any(word in var_lower for word in ['log', 'debug']):
            return "Logging"
        elif any(word in var_lower for word in ['port', 'host', 'server']):
            return "Network"
        else:
            return "General"

    @staticmethod
    def _generate_table_recommendations_static(data: dict) -> None:
        """Generate recommendations for table view."""
        # Check for large profiles
        large_profiles = [p for p in data["profile_breakdown"] if p["size"] > 10000]
        if large_profiles:
            data["recommendations"].append(f"💡 {len(large_profiles)} large profiles (>10KB) detected")

        # Check for profiles with many variables
        heavy_profiles = [p for p in data["profile_breakdown"] if p["variables"] > 50]
        if heavy_profiles:
            data["recommendations"].append(f"💡 {len(heavy_profiles)} profiles with many variables (>50)")

        # Check for low variable profiles
        empty_profiles = [p for p in data["profile_breakdown"] if p["variables"] < 5]
        if empty_profiles:
            data["recommendations"].append(f"💡 {len(empty_profiles)} very small profiles (<5 variables)")

        # Check sensitive variable distribution
        total_sensitive = sum(p["sensitive_count"] for p in data["profile_breakdown"])
        if total_sensitive > data["total_variables"] * 0.3:
            data["recommendations"].append("🔒 Consider using encryption for sensitive variables")

        if data["total_profiles"] > 10:
            data["recommendations"].append("📊 Consider organizing profiles by environment")


class ProfileBatchActionsModal(ModalScreen):
    """Batch actions modal for managing multiple profiles."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.profiles = list_profiles()

    def compose(self) -> ComposeResult:
        """Compose the batch actions modal."""
        with Container():
            yield Static("🗂️ Batch Profile Actions", classes="modal-title")
            
            # Profile selection
            yield Static("Select Profiles:", classes="info-label")
            
            # Create checkboxes for profile selection
            self.selected_profiles = set()
            for profile in self.profiles:
                is_active = profile == get_current_profile()
                checkbox = Button(
                    f"{'✓' if is_active else '○'} {profile}",
                    variant="default" if not is_active else "success",
                    id=f"select-{profile}",
                    classes="profile-checkbox"
                )
                if is_active:
                    checkbox.disabled = True  # Can't batch modify active profile
                yield checkbox
            
            # Action selection
            yield Static("\\nChoose Action:", classes="info-label")
            
            with Vertical(classes="action-options"):
                yield Button("🔄 Switch All to Profile", variant="primary", id="switch-all-btn")
                yield Button("📤 Export Selected", variant="default", id="export-selected-btn")
                yield Button("📥 Import to All", variant="default", id="import-all-btn")
                yield Button("🧹 Clean All", variant="warning", id="clean-all-btn")
                yield Button("🗑️ Delete Selected", variant="error", id="delete-selected-btn")
                yield Button("🔗 Duplicate Profiles", variant="default", id="duplicate-profiles-btn")
            
            # Close button
            yield Button("❌ Close", variant="default", id="close-batch-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "close-batch-btn":
            self.dismiss()
        elif button_id == "switch-all-btn":
            self.switch_all_profiles()
        elif button_id == "export-selected-btn":
            self.export_selected()
        elif button_id == "import-all-btn":
            self.import_to_all()
        elif button_id == "clean-all-btn":
            self.clean_all()
        elif button_id == "delete-selected-btn":
            self.delete_selected()
        elif button_id == "duplicate-profiles-btn":
            self.duplicate_profiles()
        elif button_id and button_id.startswith("select-"):
            profile = button_id.replace("select-", "")
            self.toggle_profile_selection(profile)

    def toggle_profile_selection(self, profile: str) -> None:
        """Toggle profile selection."""
        if profile in self.selected_profiles:
            self.selected_profiles.remove(profile)
            button = self.query_one(f"#select-{profile}", Button)
            button.label = f"○ {profile}"
            button.variant = "default"
        else:
            self.selected_profiles.add(profile)
            button = self.query_one(f"#select-{profile}", Button)
            button.label = f"✓ {profile}"
            button.variant = "success"

    def switch_all_profiles(self) -> None:
        """Switch all selected profiles to a specific profile."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        # For now, just switch to the first selected profile
        target_profile = list(self.selected_profiles)[0]
        from ...config import set_current_profile
        set_current_profile(target_profile)
        
        self.notify(f"✅ Switched to profile: {target_profile}", severity="success")
        self.dismiss()

    def export_selected(self) -> None:
        """Export all selected profiles."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        try:
            export_data = {}
            for profile in self.selected_profiles:
                manager = EnvManager(profile)
                export_data[profile] = manager.load_env()
            
            export_file = Path.home() / f"envcli_batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.notify(f"✅ Exported {len(self.selected_profiles)} profiles to {export_file}", severity="success")
            self.dismiss()
        except Exception as e:
            self.notify(f"❌ Export failed: {e}", severity="error")

    def import_to_all(self) -> None:
        """Import variables to all selected profiles."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        self.notify("📥 Import to All - Opening import dialog...", severity="information")
        self.app.push_screen(ProfileImportModal())

    def clean_all(self) -> None:
        """Clean all selected profiles."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        self.notify("🧹 Clean All - Opening clean dialog...", severity="information")
        self.app.push_screen(ProfileCleanModal())

    def delete_selected(self) -> None:
        """Delete all selected profiles."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        if get_current_profile() in self.selected_profiles:
            self.notify("❌ Cannot delete active profile", severity="error")
            return
        
        # Confirmation
        count = len(self.selected_profiles)
        if self.selected_profiles:
            profiles_list = ", ".join(list(self.selected_profiles)[:3])
            if count > 3:
                profiles_list += f" (+{count-3} more)"
            
            self.notify(f"🗑️ This will delete {count} profiles: {profiles_list}", severity="warning")
            
            # Perform deletion
            deleted_count = 0
            for profile in self.selected_profiles.copy():
                try:
                    if profile != get_current_profile():
                        profile_file = PROFILES_DIR / f"{profile}.json"
                        if profile_file.exists():
                            profile_file.unlink()
                            self.selected_profiles.remove(profile)
                            deleted_count += 1
                except Exception as e:
                    self.notify(f"❌ Failed to delete {profile}: {e}", severity="error")
            
            if deleted_count > 0:
                self.notify(f"✅ Deleted {deleted_count} profiles", severity="success")
                self.dismiss()

    def duplicate_profiles(self) -> None:
        """Duplicate selected profiles with new names."""
        if not self.selected_profiles:
            self.notify("Please select at least one profile", severity="error")
            return
        
        # For now, just create copies with "_copy" suffix
        duplicated_count = 0
        for profile in self.selected_profiles:
            try:
                new_name = f"{profile}_copy"
                counter = 1
                while new_name in list_profiles():
                    new_name = f"{profile}_copy_{counter}"
                    counter += 1
                
                # Copy profile
                create_profile(new_name)
                source_manager = EnvManager(profile)
                target_manager = EnvManager(new_name)
                env_vars = source_manager.load_env()
                target_manager.save_env(env_vars)
                
                duplicated_count += 1
            except Exception as e:
                self.notify(f"❌ Failed to duplicate {profile}: {e}", severity="error")
        
        if duplicated_count > 0:
            self.notify(f"✅ Duplicated {duplicated_count} profiles", severity="success")
            self.dismiss()
