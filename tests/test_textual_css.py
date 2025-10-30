#!/usr/bin/env python3
"""
More comprehensive test to validate CSS with Textual's parser
"""

from textual.css.parse import parse_css
from textual.css.stylesheet import Stylesheet
from src.envcli.tui.theme import TUI_CSS
from src.envcli.tui.themes import generate_css, THEMES


def test_textual_css_parsing():
    """Test if the CSS can be parsed by Textual's parser"""
    print("Testing Textual CSS parsing...")
    
    try:
        # Test the main CSS from theme.py
        print("  Testing main TUI_CSS...")
        parsed_main = parse_css(TUI_CSS, path="<test>")
        print(f"  ✓ Main CSS parsed successfully: {len(parsed_main)} rules")
        
        # Test CSS generation for each theme
        for theme_name in THEMES:
            colors = THEMES[theme_name]
            css_content = generate_css(colors)
            
            print(f"  Testing generated CSS for '{theme_name}'...")
            parsed_theme = parse_css(css_content, path="<test>")
            print(f"  ✓ Theme '{theme_name}' CSS parsed successfully: {len(parsed_theme)} rules")
            
        print(f"  ✓ Successfully parsed CSS for main theme and {len(THEMES)} additional themes")
        return True
        
    except Exception as e:
        print(f"  ✗ CSS parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stylesheet_loading():
    """Test loading CSS into a Stylesheet object"""
    print("\nTesting Stylesheet loading...")
    
    try:
        # Create a stylesheet and load the CSS
        stylesheet = Stylesheet()
        
        # Load the main CSS
        print("  Loading main TUI_CSS into Stylesheet...")
        stylesheet.parse(TUI_CSS, path="<test>")
        print("  ✓ Main CSS loaded into Stylesheet successfully")
        
        # Load a generated theme CSS
        sample_css = generate_css(THEMES['github_dark'])
        print("  Loading generated theme CSS into Stylesheet...")
        stylesheet.parse(sample_css, path="<test2>")
        print("  ✓ Generated theme CSS loaded into Stylesheet successfully")
        
        print("  ✓ Stylesheet loading test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Stylesheet loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Running comprehensive CSS validation tests...\n")
    
    success = True
    success &= test_textual_css_parsing()
    success &= test_stylesheet_loading()
    
    if success:
        print("\n🎉 All CSS validation tests passed!")
        print("The StylesheetParseError has been successfully fixed.")
    else:
        print("\n❌ Some CSS validation tests failed.")
        
    return success


if __name__ == "__main__":
    main()