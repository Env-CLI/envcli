"""Variables management screen for EnvCLI TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Input, DataTable, Label
from textual.message import Message
from rich.text import Text
from typing import Optional, List
from pathlib import Path
import os

from ...config import (
    list_profiles,
    create_profile,
    get_current_profile,
    set_current_profile,
    PROFILES_DIR
)
from ...env_manager import EnvManager


class ProfileCard(Container):
    """Card displaying profile information."""
    
    def __init__(self, profile_name: str, is_active: bool = False):
        super().__init__()
        self.profile_name = profile_name
        self.is_active = is_active
        self.manager = EnvManager(profile_name)
        
        # Get profile metadata
        self.var_count = len(self.manager.load_env())
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        self.last_modified = "Unknown"
        if profile_file.exists():
            mtime = os.path.getmtime(profile_file)
            from datetime import datetime
            self.last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    
    def compose(self) -> ComposeResult:
        """Compose the profile card."""
        # Card title with active indicator
        title = Text()
        if self.is_active:
            title.append("+ ", style="bold #00E676")
        title.append(self.profile_name, style="bold #00E676" if self.is_active else "bold #64FFDA")
        yield Static(title, classes="profile-card-title")

        # Metadata
        meta = Text()
        meta.append(f"= Variables: ", style="#757575")
        meta.append(f"{self.var_count}  ", style="#00E676")
        meta.append(f"o Modified: ", style="#757575")
        meta.append(self.last_modified, style="#64FFDA")
        yield Static(meta, classes="profile-card-meta")

        # Action buttons
        with Horizontal(classes="profile-card-actions"):
            if not self.is_active:
                yield Button("Switch", variant="primary", id=f"switch-{self.profile_name}")
            yield Button("Compare", variant="default", id=f"compare-{self.profile_name}")
            yield Button("Delete", variant="error", id=f"delete-{self.profile_name}")


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
    """Main profiles management screen."""
    
    def __init__(self):
        super().__init__()
        self.current_profile = get_current_profile()
        self.show_creator = False
        self.show_comparison = False
        self.comparison_profile = None
    
    def compose(self) -> ComposeResult:
        """Compose the profiles screen."""
        # Header
        yield Static("Profile Management", classes="screen-title")
        
        # Stats bar
        profiles = list_profiles()
        stats_text = Text()
        stats_text.append(f"/ Total Profiles: ", style="#757575")
        stats_text.append(f"{len(profiles)}", style="bold #00E676")
        stats_text.append(f"  |  + Active: ", style="#757575")
        stats_text.append(self.current_profile, style="bold #00E676")
        yield Static(stats_text, classes="stats-bar")
        
        # Action buttons
        with Horizontal(classes="action-bar"):
            yield Button("+ Create Profile", variant="success", id="create-profile-btn")
            yield Button("@ Refresh", variant="default", id="refresh-profiles-btn")
            yield Button("= View All", variant="default", id="view-all-btn")
        
        # Main content area
        with Vertical(classes="content-area"):
            # Profile list (scrollable)
            with VerticalScroll(classes="profile-list"):
                yield from self._create_profile_list()
    
    def _create_profile_list(self):
        """Yield profile cards."""
        profiles = list_profiles()
        self.app.log(f"Creating profile list with {len(profiles)} profiles: {profiles}")

        for profile in profiles:
            is_active = (profile == self.current_profile)
            self.app.log(f"Creating ProfileCard for {profile} (active={is_active})")
            yield ProfileCard(profile, is_active)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Log for debugging
        self.app.log(f"ProfilesScreen: Button pressed: {button_id}")

        if button_id == "create-profile-btn":
            self.app.log("Creating profile...")
            self.show_profile_creator()
        elif button_id == "refresh-profiles-btn":
            self.app.log("Refreshing profiles...")
            self.app.notify("Refreshing profiles...", severity="information")
            self.run_worker(self.refresh_profiles())
        elif button_id == "view-all-btn":
            self.app.log("Viewing all profiles...")
            self.show_all_profiles()
        elif button_id and button_id.startswith("switch-"):
            profile_name = button_id.replace("switch-", "")
            self.app.log(f"Switching to profile: {profile_name}")
            self.app.notify(f"Switching to profile: {profile_name}", severity="information")
            self.run_worker(self.switch_profile(profile_name))
        elif button_id and button_id.startswith("compare-"):
            profile_name = button_id.replace("compare-", "")
            self.app.log(f"Comparing profile: {profile_name}")
            self.show_comparison_view(profile_name)
        elif button_id and button_id.startswith("delete-"):
            profile_name = button_id.replace("delete-", "")
            self.app.log(f"Deleting profile: {profile_name}")
            self.app.notify(f"Deleting profile: {profile_name}", severity="warning")
            self.run_worker(self.delete_profile(profile_name))
        elif button_id == "close-comparison-btn":
            self.run_worker(self._remove_comparison())
    
    def show_profile_creator(self) -> None:
        """Show the profile creator form."""
        # Mount creator as an overlay
        self.run_worker(self._mount_creator())

    async def _mount_creator(self) -> None:
        """Mount the profile creator form."""
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
        """Refresh the profile list."""
        # Update stats bar
        profiles = list_profiles()
        stats_text = Text()
        stats_text.append(f"/ Total Profiles: ", style="#757575")
        stats_text.append(f"{len(profiles)}", style="bold #00E676")
        stats_text.append(f"  |  + Active: ", style="#757575")
        stats_text.append(self.current_profile, style="bold #00E676")

        try:
            stats_bar = self.query_one(".stats-bar", Static)
            stats_bar.update(stats_text)
        except:
            pass

        # Remove old list
        old_list = self.query_one(".profile-list", VerticalScroll)
        await old_list.remove()

        # Create new list with profile cards
        content_area = self.query_one(".content-area", Vertical)
        new_list = VerticalScroll(classes="profile-list")
        await content_area.mount(new_list)

        # Mount profile cards
        for profile in profiles:
            is_active = (profile == self.current_profile)
            await new_list.mount(ProfileCard(profile, is_active))
        
        # Update stats
        self.current_profile = get_current_profile()
        profiles = list_profiles()
        stats_text = Text()
        stats_text.append(f"/ Total Profiles: ", style="#757575")
        stats_text.append(f"{len(profiles)}", style="bold #00E676")
        stats_text.append(f"  |  + Active: ", style="#757575")
        stats_text.append(self.current_profile, style="bold #00E676")
        
        stats_bar = self.query_one(".stats-bar", Static)
        stats_bar.update(stats_text)
    
    def show_all_profiles(self) -> None:
        """Show all profiles in a table view."""
        # TODO: Implement table view
        pass
    
    async def switch_profile(self, profile_name: str) -> None:
        """Switch to a different profile."""
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

        # Show success message
        self.app.notify(f"+ Switched to profile: {profile_name}", severity="information")
        self.app.log(f"Profile switch complete")
    
    def show_comparison_view(self, profile_name: str) -> None:
        """Show comparison between current and selected profile."""
        self.comparison_profile = profile_name
        self.run_worker(self._mount_comparison(profile_name))

    async def _mount_comparison(self, profile_name: str) -> None:
        """Mount the profile comparison view."""
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
    
    async def delete_profile(self, profile_name: str) -> None:
        """Delete a profile."""
        if profile_name == self.current_profile:
            self.app.notify(f"Cannot delete active profile: {profile_name}", severity="error")
            return

        # Delete the profile file
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        if profile_file.exists():
            profile_file.unlink()
            self.app.notify(f"+ Deleted profile: {profile_name}", severity="information")

        # Refresh the display
        await self.refresh_profiles()
