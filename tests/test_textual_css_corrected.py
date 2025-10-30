#!/usr/bin/env python3
"""
More comprehensive test to validate CSS with Textual's parser
"""

from textual.css.stylesheet import Stylesheet
from src.envcli.tui.theme import TUI_CSS
from src.envcli.tui.themes import generate_css, THEMES


def test_stylesheet_parsing():
    """Test if the CSS can be parsed by Textual's Stylesheet"""
    print("Testing Textual Stylesheet parsing...")
    
    try:
        # Test the main CSS from theme.py
        print("  Testing main TUI_CSS...")
        stylesheet = Stylesheet()
        stylesheet.parse(TUI_CSS, path="theme.py")
        print(f"  ✓ Main CSS parsed successfully")
        
        # Test CSS generation for each theme
        for theme_name in THEMES:
            colors = THEMES[theme_name]
            css_content = generate_css(colors)
            
            print(f"  Testing generated CSS for '{theme_name}'...")
            theme_stylesheet = Stylesheet()
            theme_stylesheet.parse(css_content, path=f"{theme_name}.css")
            print(f"  ✓ Theme '{theme_name}' CSS parsed successfully")
            
        print(f"  ✓ Successfully parsed CSS for main theme and {len(THEMES)} additional themes")
        return True
        
    except Exception as e:
        print(f"  ✗ CSS parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Running comprehensive CSS validation tests...\n")
    
    success = True
    success &= test_stylesheet_parsing()
    
    if success:
        print("\n🎉 All CSS validation tests passed!")
        print("The StylesheetParseError has been successfully fixed.")
        print("\nSummary of fixes applied:")
        print("1. Fixed invalid character in status icons: changed 'info': 'vFO' to 'info': 'ℹ'")
        print("2. Removed duplicate .creator-title CSS rule")
    else:
        print("\n❌ Some CSS validation tests failed.")
        
    return success


if __name__ == "__main__":
    main()