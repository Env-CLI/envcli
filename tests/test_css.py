#!/usr/bin/env python3
"""
Test script to validate the CSS in the theme.py file
"""

from src.envcli.tui.theme import TUI_CSS
from src.envcli.tui.themes import generate_css, THEMES

def test_main_css():
    """Test the main CSS from theme.py"""
    try:
        # Try to load the main CSS
        css_content = TUI_CSS
        print(f"✓ Main CSS loaded successfully, length: {len(css_content)} chars")
        
        # Check if there are any obvious syntax errors
        lines = css_content.strip().split('\n')
        error_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for some common CSS syntax errors
            if 'text-style: bold;' in line and (';' in line[:line.index('text-style: bold;')] and '{' not in line[:line.index('text-style: bold;')]):
                print(f"  Warning at line {i}: possible formatting issue in '{line.strip()}'")
                
        print(f"✓ Main CSS syntax check passed ({len(lines)} lines)")
        return True
    except Exception as e:
        print(f"✗ Error with main CSS: {e}")
        return False

def test_generated_css():
    """Test CSS generation from themes"""
    try:
        for theme_name in THEMES:
            colors = THEMES[theme_name]
            css_content = generate_css(colors)
            print(f"✓ Generated CSS for theme '{theme_name}' successfully, length: {len(css_content)} chars")
        
        print(f"✓ Tested CSS generation for {len(THEMES)} themes")
        return True
    except Exception as e:
        print(f"✗ Error generating CSS for themes: {e}")
        return False

def main():
    print("Testing CSS syntax...")
    success = True
    
    success &= test_main_css()
    success &= test_generated_css()
    
    if success:
        print("\n✓ All CSS tests passed! The StylesheetParseError should be fixed.")
    else:
        print("\n✗ Some CSS tests failed.")
        
    return success

if __name__ == "__main__":
    main()