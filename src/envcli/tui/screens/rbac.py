"""
RBAC & Policy Management Screen for EnvCLI TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button, DataTable, Input, Select, Label
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.message import Message
from ...rbac import RBACManager, Role, Permission
from ...policy_engine import PolicyEngine


class RBACScreen(Container):
    """RBAC & Policy management screen."""

    DEFAULT_CSS = """
    RBACScreen {
        background: $surface;
    }

    #rbac-header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
        text-style: bold;
    }

    #rbac-content {
        height: 100%;
        overflow-y: auto;
    }

    .section-title {
        background: $panel;
        color: $text;
        height: 3;
        content-align: left middle;
        padding: 0 2;
        text-style: bold;
    }

    .rbac-status {
        height: 3;
        background: $panel;
        padding: 0 2;
        margin: 1 0;
    }

    .users-table {
        height: 15;
        margin: 1 2;
    }

    .add-user-form {
        height: auto;
        background: $panel;
        padding: 1 2;
        margin: 1 2;
    }

    .permissions-matrix {
        height: 15;
        margin: 1 2;
    }

    .policies-table {
        height: 12;
        margin: 1 2;
    }

    .button-row {
        height: 3;
        margin: 1 2;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.rbac_manager = RBACManager()
        self.policy_engine = PolicyEngine()

    def compose(self) -> ComposeResult:
        """Compose the RBAC screen."""
        yield Static("@ RBAC & Policy Management", id="rbac-header")

        with VerticalScroll(id="rbac-content"):
            # RBAC Status
            yield Static("🔐 RBAC Status", classes="section-title")
            yield Container(
                Static(self._get_rbac_status(), id="rbac-status-text"),
                classes="rbac-status"
            )

            # Enable/Disable RBAC buttons
            with Horizontal(classes="button-row"):
                yield Button("+ Enable RBAC", id="enable-rbac-btn", variant="success")
                yield Button("❌ Disable RBAC", id="disable-rbac-btn", variant="error")
                yield Button("🔄 Reset RBAC", id="reset-rbac-btn", variant="error")
                yield Button("@ Refresh", id="refresh-rbac-btn", variant="primary")

            # Users Section
            # Session Section
            yield Static("🔑 Session", classes="section-title")
            with Container(classes="add-user-form"):
                yield Label("Login")
                yield Label("Username:")
                yield Input(placeholder="Enter username", id="login-username")
                yield Label("Password:")
                yield Input(placeholder="Enter password", id="login-password", password=True)
                with Horizontal(classes="button-row"):
                    yield Button("Login", id="login-btn", variant="primary")
                    yield Button("Logout", id="logout-btn", variant="warning")
                    yield Button("Who am I", id="whoami-btn", variant="primary")
                yield Label("Quick Setup (Enable RBAC + Create Admin)")
                yield Input(placeholder="Admin username (default: admin)", id="qs-username")
                yield Input(placeholder="Admin password", id="qs-password", password=True)
                yield Input(placeholder="Confirm password", id="qs-confirm", password=True)
                with Horizontal(classes="button-row"):
                    yield Button("Quick Setup", id="quick-setup-btn", variant="success")
                yield Label("Change Password")
                yield Input(placeholder="Current password", id="cp-old", password=True)
                yield Input(placeholder="New password", id="cp-new", password=True)
                yield Input(placeholder="Confirm new password", id="cp-confirm", password=True)
                with Horizontal(classes="button-row"):
                    yield Button("Change Password", id="change-password-btn", variant="primary")

            yield Static("Set Password for Selected User", classes="section-title")
            with Container(classes="add-user-form"):
                yield Input(placeholder="New password", id="sp-new", password=True)
                yield Input(placeholder="Confirm password", id="sp-confirm", password=True)
                with Horizontal(classes="button-row"):
                    yield Button("Set Password for Selected", id="set-password-btn", variant="primary")

            yield Static("👥 User Management", classes="section-title")

            # User Search/Filter
            with Container(classes="add-user-form"):
                yield Label("Search Users:")
                yield Input(placeholder="Type to filter users...", id="user-search-input")

            yield DataTable(id="users-table", classes="users-table")

            # Add User Form
            yield Static("+ Add User", classes="section-title")
            with Container(classes="add-user-form"):
                yield Label("Username:")
                yield Input(placeholder="Enter username", id="username-input")
                yield Label("Role:")
                yield Select(
                    [(role.value.title(), role.value) for role in Role],
                    id="role-select",
                    prompt="Select role"
                )
                yield Label("Initial Password (optional):")
                yield Input(placeholder="Set initial password (optional)", id="user-password-input", password=True)
                with Horizontal(classes="button-row"):
                    yield Button("+ Add User", id="add-user-btn", variant="success")
                    yield Button("🗑️ Remove Selected User", id="remove-user-btn", variant="error")
                    yield Button("@ Change Role", id="change-role-btn", variant="primary")

            # Permissions Matrix
            yield Static("🔑 Permissions Matrix", classes="section-title")
            yield DataTable(id="permissions-table", classes="permissions-matrix")

            # Policies Section
            yield Static("- Active Policies", classes="section-title")
            yield DataTable(id="policies-table", classes="policies-table")

            with Horizontal(classes="button-row"):
                yield Button("- View All Policies", id="view-policies-btn", variant="primary")
                yield Button("O View Audit Log", id="view-audit-btn", variant="primary")

    def on_mount(self) -> None:
        """Initialize tables when screen is mounted."""
        self._setup_users_table()
        self._setup_permissions_table()
        self._setup_policies_table()
        self._load_users()
        self._load_permissions()
        self._load_policies()

    def _get_rbac_status(self) -> str:
        """Get RBAC status text."""
        enabled = self.rbac_manager.is_enabled()
        status = "+ Enabled" if enabled else "❌ Disabled"
        user_count = len(self.rbac_manager.list_users())
        current_user = self.rbac_manager.get_current_user() or "<none>"
        return f"Status: {status} | Users: {user_count} | Current User: {current_user}"

    def _setup_users_table(self) -> None:
        """Setup users table columns."""
        table = self.query_one("#users-table", DataTable)
        table.add_columns("Username", "Role", "Added By", "Added At", "Last Active")

    def _setup_permissions_table(self) -> None:
        """Setup permissions matrix table."""
        table = self.query_one("#permissions-table", DataTable)
        table.add_columns("Permission", "Admin", "Member", "Guest")

    def _setup_policies_table(self) -> None:
        """Setup policies table columns."""
        table = self.query_one("#policies-table", DataTable)
        table.add_columns("Type", "Pattern/Convention", "Description")

    async def _load_users(self) -> None:
        """Load users into the table."""
        table = self.query_one("#users-table", DataTable)
        table.clear()

        users = self.rbac_manager.list_users()
        for user in users:
            table.add_row(
                user["username"],
                user["role"],
                user.get("added_by", "N/A"),
                user.get("added_at", "N/A")[:19],  # Truncate timestamp
                user.get("last_active", "N/A")[:19]
            )

    async def _load_permissions(self) -> None:
        """Load permissions matrix."""
        table = self.query_one("#permissions-table", DataTable)
        table.clear()

        # Get permissions for each role
        admin_perms = set(self.rbac_manager.get_role_permissions(Role.ADMIN))
        member_perms = set(self.rbac_manager.get_role_permissions(Role.MEMBER))
        guest_perms = set(self.rbac_manager.get_role_permissions(Role.GUEST))

        # Add row for each permission
        for perm in Permission:
            table.add_row(
                perm.value,
                "+" if perm.value in admin_perms else "❌",
                "+" if perm.value in member_perms else "❌",
                "+" if perm.value in guest_perms else "❌"
            )

    async def _load_policies(self) -> None:
        """Load active policies."""
        table = self.query_one("#policies-table", DataTable)
        table.clear()

        policies = self.policy_engine.policies

        # Add required keys
        for policy in policies.get("required_keys", []):
            table.add_row(
                "Required Key",
                policy["pattern"],
                policy.get("description", "N/A")
            )

        # Add prohibited patterns
        for policy in policies.get("prohibited_patterns", []):
            table.add_row(
                "Prohibited Pattern",
                policy["pattern"],
                policy.get("description", "N/A")
            )

        # Add naming conventions
        for policy in policies.get("naming_conventions", []):
            table.add_row(
                "Naming Convention",
                policy["convention"],
                policy.get("description", "N/A")
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "enable-rbac-btn":
            await self._enable_rbac()
        elif button_id == "disable-rbac-btn":
            await self._disable_rbac()
        elif button_id == "reset-rbac-btn":
            await self._reset_rbac()
        elif button_id == "refresh-rbac-btn":
            await self._refresh_all()
        elif button_id == "add-user-btn":
            await self._add_user()
        elif button_id == "remove-user-btn":
            await self._remove_user()
        elif button_id == "change-role-btn":
            await self._change_role()
        elif button_id == "login-btn":
            await self._login()
        elif button_id == "logout-btn":
            await self._logout()
        elif button_id == "whoami-btn":
            current = self.rbac_manager.get_current_user()
            who = current if current else "<not logged in>"
            self.app.notify(f"Current user: {who}", severity="information")
        elif button_id == "quick-setup-btn":
            await self._quick_setup()
        elif button_id == "change-password-btn":
            await self._change_password()
        elif button_id == "set-password-btn":
            await self._set_password_for_selected()
        elif button_id == "user-details-btn":
            await self._show_user_details()
        elif button_id == "view-policies-btn":
            self.app.notify("Policy editor coming soon!", severity="information")
        elif button_id == "view-audit-btn":
            await self._view_audit_log()

    async def _enable_rbac(self) -> None:
        """Enable RBAC system."""
        self.rbac_manager.enable_rbac()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify("+ RBAC enabled", severity="information")

    async def _disable_rbac(self) -> None:
        """Disable RBAC system."""
        self.rbac_manager.disable_rbac()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify("❌ RBAC disabled", severity="warning")

    async def _reset_rbac(self) -> None:
        """Reset RBAC system to factory defaults."""
        # Show confirmation dialog
        from textual.screen import ModalScreen
        from textual.containers import Container, Vertical
        from textual.widgets import Label

        class ConfirmResetScreen(ModalScreen[bool]):
            """Confirmation dialog for RBAC reset."""

            DEFAULT_CSS = """
            ConfirmResetScreen {
                align: center middle;
            }

            ConfirmResetScreen > Container {
                width: 60;
                height: auto;
                background: $surface;
                border: thick $error;
                padding: 1 2;
            }

            ConfirmResetScreen Label {
                width: 100%;
                content-align: center middle;
                margin: 1 0;
            }

            ConfirmResetScreen .warning-text {
                color: $warning;
                text-style: bold;
            }

            ConfirmResetScreen .info-text {
                color: $text-muted;
            }

            ConfirmResetScreen Horizontal {
                width: 100%;
                height: auto;
                align: center middle;
                margin-top: 1;
            }

            ConfirmResetScreen Button {
                margin: 0 1;
            }
            """

            def compose(self):
                with Container():
                    yield Label("⚠️  RESET RBAC SYSTEM", classes="warning-text")
                    yield Label("This will delete ALL RBAC data:", classes="info-text")
                    yield Label("• All users and passwords", classes="info-text")
                    yield Label("• All sessions (you will be logged out)", classes="info-text")
                    yield Label("• All audit logs", classes="info-text")
                    yield Label("• All custom role permissions", classes="info-text")
                    yield Label("")
                    yield Label("Are you sure?", classes="warning-text")
                    with Horizontal():
                        yield Button("Yes, Reset", id="confirm-yes", variant="error")
                        yield Button("Cancel", id="confirm-no", variant="primary")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "confirm-yes":
                    self.dismiss(True)
                else:
                    self.dismiss(False)

        # Show confirmation dialog
        result = await self.app.push_screen_wait(ConfirmResetScreen())

        if result:
            if self.rbac_manager.reset_rbac():
                self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
                await self._load_users()
                await self._load_permissions()
                await self._load_policies()
                self.app.notify("🔄 RBAC system reset to factory defaults", severity="warning", timeout=5)
                self.app.notify("💡 Run Quick Setup to configure RBAC again", severity="information", timeout=5)
            else:
                self.app.notify("❌ Failed to reset RBAC system", severity="error")

    async def _refresh_all(self) -> None:
        """Refresh all data."""
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        await self._load_users()
        await self._load_permissions()
        await self._load_policies()
        self.app.notify("@ Data refreshed", severity="information")

    async def _add_user(self) -> None:
        """Add a new user."""
        username_input = self.query_one("#username-input", Input)
        role_select = self.query_one("#role-select", Select)

        username = username_input.value.strip()
        role_value = role_select.value

        if not username:
            self.app.notify("❌ Username is required", severity="error")
            return

        if role_value == Select.BLANK:
            self.app.notify("❌ Please select a role", severity="error")
            return

        try:
            role = Role(role_value)
            current_user = self.rbac_manager.get_current_user() or "system"
            # Optional initial password from input (if provided)
            try:
                pwd_input = self.query_one("#user-password-input", Input)
                initial_password = pwd_input.value.strip()
            except Exception:
                initial_password = ""
            self.rbac_manager.add_user(username, role, current_user, password=initial_password or None)
            await self._load_users()
            self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
            username_input.value = ""
            if 'pwd_input' in locals():
                pwd_input.value = ""
            note = " (no password set; user cannot log in until password is set)" if not initial_password else ""
            self.app.notify(f"+ User '{username}' added with role '{role.value}'{note}", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Error adding user: {e}", severity="error")

    async def _remove_user(self) -> None:
        """Remove selected user."""
        table = self.query_one("#users-table", DataTable)
        if table.cursor_row is None:
            self.app.notify("❌ Please select a user to remove", severity="error")
            return

        row_key = table.cursor_row
        username = table.get_row(row_key)[0]

        current_user = self.rbac_manager.get_current_user() or "system"
        self.rbac_manager.remove_user(username, current_user)
        await self._load_users()
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
        self.app.notify(f"+ User '{username}' removed", severity="information")

    async def _change_role(self) -> None:
        """Change role of selected user."""
        table = self.query_one("#users-table", DataTable)
        role_select = self.query_one("#role-select", Select)

        if table.cursor_row is None:
            self.app.notify("❌ Please select a user", severity="error")
            return

        role_value = role_select.value
        if role_value == Select.BLANK:
            self.app.notify("❌ Please select a new role", severity="error")
            return

        row_key = table.cursor_row
        username = table.get_row(row_key)[0]

        try:
            new_role = Role(role_value)
            current_user = self.rbac_manager.get_current_user() or "system"
            self.rbac_manager.change_user_role(username, new_role, current_user)
            await self._load_users()
            self.app.notify(f"+ User '{username}' role changed to '{new_role.value}'", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Error changing role: {e}", severity="error")

    async def _view_audit_log(self) -> None:
        """View audit log."""
        log_entries = self.rbac_manager.get_audit_log(limit=10)
        if log_entries:
            message = "O Recent Audit Log:\n"
            for entry in log_entries[-5:]:  # Show last 5
                timestamp = entry['timestamp'][:19]
                message += f"\n{timestamp} | {entry['performed_by']} | {entry['action']}"
            self.app.notify(message, severity="information", timeout=10)
        else:
            self.app.notify("No audit log entries", severity="information")

    async def _login(self) -> None:
        """Handle login."""
        username_input = self.query_one("#login-username", Input)
        password_input = self.query_one("#login-password", Input)

        username = username_input.value.strip()
        password = password_input.value

        if not username:
            self.app.notify("❌ Username is required", severity="error")
            return

        if not password:
            self.app.notify("❌ Password is required", severity="error")
            return

        if not self.rbac_manager.is_enabled():
            self.app.notify("❌ RBAC is disabled. Use Quick Setup first.", severity="error")
            return

        if self.rbac_manager.login(username, password):
            self.app.notify(f"✓ Logged in as '{username}'", severity="information")
            self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
            username_input.value = ""
            password_input.value = ""
            await self._load_users()
        else:
            self.app.notify("❌ Invalid credentials", severity="error")
            password_input.value = ""

    async def _logout(self) -> None:
        """Handle logout."""
        current = self.rbac_manager.get_current_user()
        if not current:
            self.app.notify("❌ Not logged in", severity="warning")
            return

        self.rbac_manager.logout()
        self.app.notify(f"✓ Logged out", severity="information")
        self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())

    async def _quick_setup(self) -> None:
        """Handle quick setup: enable RBAC, create admin, and login."""
        username_input = self.query_one("#qs-username", Input)
        password_input = self.query_one("#qs-password", Input)
        confirm_input = self.query_one("#qs-confirm", Input)

        username = username_input.value.strip() or "admin"
        password = password_input.value
        confirm = confirm_input.value

        if not password:
            self.app.notify("❌ Password is required", severity="error")
            return

        if password != confirm:
            self.app.notify("❌ Passwords do not match", severity="error")
            confirm_input.value = ""
            return

        try:
            # Enable RBAC
            self.rbac_manager.enable_rbac()

            # Create admin user with password
            self.rbac_manager.add_user(username, Role.ADMIN, added_by=username, password=password)

            # Log in as that user
            if self.rbac_manager.login(username, password):
                self.app.notify(f"✓ RBAC enabled, admin '{username}' created, and logged in", severity="information")
                self.query_one("#rbac-status-text", Static).update(self._get_rbac_status())
                username_input.value = ""
                password_input.value = ""
                confirm_input.value = ""
                await self._load_users()
                await self._load_permissions()
                await self._load_policies()
            else:
                self.app.notify("❌ Setup succeeded but login failed", severity="error")
        except Exception as e:
            self.app.notify(f"❌ Quick setup failed: {e}", severity="error")

    async def _change_password(self) -> None:
        """Handle change password for current user."""
        old_input = self.query_one("#cp-old", Input)
        new_input = self.query_one("#cp-new", Input)
        confirm_input = self.query_one("#cp-confirm", Input)

        current_user = self.rbac_manager.get_current_user()
        if not current_user:
            self.app.notify("❌ Not logged in. Please login first.", severity="error")
            return

        old_password = old_input.value
        new_password = new_input.value
        confirm = confirm_input.value

        if not old_password:
            self.app.notify("❌ Current password is required", severity="error")
            return

        if not new_password:
            self.app.notify("❌ New password is required", severity="error")
            return

        if new_password != confirm:
            self.app.notify("❌ New passwords do not match", severity="error")
            confirm_input.value = ""
            return

        if self.rbac_manager.change_password(current_user, old_password, new_password):
            self.app.notify("✓ Password changed successfully", severity="information")
            old_input.value = ""
            new_input.value = ""
            confirm_input.value = ""
        else:
            self.app.notify("❌ Failed to change password (current password incorrect)", severity="error")
            old_input.value = ""

    async def _set_password_for_selected(self) -> None:
        """Handle set password for selected user (admin operation)."""
        table = self.query_one("#users-table", DataTable)
        if table.cursor_row is None:
            self.app.notify("❌ Please select a user first", severity="error")
            return

        row_key = table.cursor_row
        username = table.get_row(row_key)[0]

        new_input = self.query_one("#sp-new", Input)
        confirm_input = self.query_one("#sp-confirm", Input)

        new_password = new_input.value
        confirm = confirm_input.value

        if not new_password:
            self.app.notify("❌ New password is required", severity="error")
            return

        if new_password != confirm:
            self.app.notify("❌ Passwords do not match", severity="error")
            confirm_input.value = ""
            return

        current_user = self.rbac_manager.get_current_user() or "system"
        if self.rbac_manager.set_user_password(username, new_password, current_user):
            self.app.notify(f"✓ Password set for user '{username}'", severity="information")
            new_input.value = ""
            confirm_input.value = ""
        else:
            self.app.notify(f"❌ Failed to set password for '{username}'", severity="error")

    async def _show_user_details(self) -> None:
        """Show detailed information for selected user."""
        table = self.query_one("#users-table", DataTable)
        if table.cursor_row is None:
            self.app.notify("❌ Please select a user first", severity="error")
            return

        row_key = table.cursor_row
        username = table.get_row(row_key)[0]

        # Get user details from RBAC manager
        users = self.rbac_manager.list_users()
        user_data = next((u for u in users if u['username'] == username), None)

        if not user_data:
            self.app.notify(f"❌ User '{username}' not found", severity="error")
            return

        # Format user details
        details = f"""👤 User Details: {username}

Role: {user_data.get('role', 'N/A')}
Added by: {user_data.get('added_by', 'N/A')}
Added at: {user_data.get('added_at', 'N/A')[:19] if user_data.get('added_at') else 'N/A'}
Last active: {user_data.get('last_active', 'N/A')[:19] if user_data.get('last_active') else 'N/A'}

Permissions: {', '.join(self.rbac_manager.get_role_permissions(Role(user_data.get('role', 'guest'))))}"""

        self.app.notify(details, severity="information", timeout=10)

