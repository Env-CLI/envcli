#!/usr/bin/env python3
"""Simple runner for EnvCLI TUI using textual."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from envcli.tui.app import EnvCLIApp

if __name__ == "__main__":
    app = EnvCLIApp()
    app.run()
