"""
Example plugin for EnvCLI.

This demonstrates how to create custom commands.
"""

def register_commands():
    """Register plugin commands."""
    return {
        "hello": hello_command,
        "greet": greet_command,
    }

def hello_command(name: str = "World"):
    """Say hello to someone."""
    print(f"Hello, {name}!")

def greet_command(name: str = "World", style: str = "formal"):
    """Greet someone in different styles."""
    if style == "formal":
        print(f"Good day, {name}!")
    elif style == "casual":
        print(f"Hey {name}!")
    else:
        print(f"Hello {name}!")
