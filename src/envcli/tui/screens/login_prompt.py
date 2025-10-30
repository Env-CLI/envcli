"""
Login Prompt Screen for EnvCLI TUI.

Shows a login screen when RBAC is enabled and user is not logged in.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label
from ...rbac import rbac_manager


class LoginPromptScreen(ModalScreen[bool]):
    """Modal screen that prompts user to log in."""
    
    DEFAULT_CSS = """
    LoginPromptScreen {
        align: center middle;
    }
    
    LoginPromptScreen > Container {
        width: 70;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 3;
    }
    
    LoginPromptScreen .title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    LoginPromptScreen .subtitle {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    LoginPromptScreen .field-label {
        width: 100%;
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
    }
    
    LoginPromptScreen Input {
        width: 100%;
        margin-bottom: 1;
    }
    
    LoginPromptScreen .button-row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }
    
    LoginPromptScreen Button {
        margin: 0 1;
        min-width: 15;
    }
    
    LoginPromptScreen .error-message {
        width: 100%;
        content-align: center middle;
        color: $error;
        margin-top: 1;
        height: auto;
    }
    """
    
    def __init__(self, message: str = "RBAC is enabled. Please log in to continue."):
        super().__init__()
        self.message = message
        self.error_message = ""
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label("🔐 Login Required", classes="title")
            yield Label(self.message, classes="subtitle")
            
            yield Label("Username:", classes="field-label")
            yield Input(placeholder="Enter your username", id="login-username")
            
            yield Label("Password:", classes="field-label")
            yield Input(placeholder="Enter your password", password=True, id="login-password")
            
            yield Static("", id="error-msg", classes="error-message")
            
            with Horizontal(classes="button-row"):
                yield Button("Login", id="login-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "login-btn":
            self._attempt_login()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        if event.input.id == "login-username":
            # Move to password field
            self.query_one("#login-password", Input).focus()
        elif event.input.id == "login-password":
            # Submit login
            self._attempt_login()
    
    def _attempt_login(self) -> None:
        """Attempt to log in with provided credentials."""
        username_input = self.query_one("#login-username", Input)
        password_input = self.query_one("#login-password", Input)
        error_msg = self.query_one("#error-msg", Static)
        
        username = username_input.value.strip()
        password = password_input.value
        
        if not username:
            error_msg.update("❌ Please enter a username")
            username_input.focus()
            return
        
        if not password:
            error_msg.update("❌ Please enter a password")
            password_input.focus()
            return
        
        # Attempt login
        if rbac_manager.login(username, password):
            self.dismiss(True)
        else:
            error_msg.update(f"❌ Invalid credentials for user '{username}'")
            password_input.value = ""
            password_input.focus()

