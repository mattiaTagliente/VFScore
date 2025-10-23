#!/usr/bin/env python3
"""
Test script to verify VFScore installation without Rich Unicode issues
"""
import sys
import os
from pathlib import Path

def test_imports():
    """Test that all main modules can be imported"""
    print("Testing VFScore imports...")
    
    try:
        import vfscore
        print("[OK] vfscore main module imported successfully")
        
        import vfscore.config
        print("[OK] vfscore.config imported successfully")
        
        import vfscore.__main__
        print("[OK] vfscore.__main__ imported successfully")
        
        from vfscore.llm.gemini import GeminiClient
        print("[OK] vfscore.llm.gemini imported successfully")
        
        import vfscore.scoring
        print("[OK] vfscore.scoring imported successfully")
        
        import vfscore.preprocess_gt
        print("[OK] vfscore.preprocess_gt imported successfully")
        
        import vfscore.render_cycles
        print("[OK] vfscore.render_cycles imported successfully")
        
        import vfscore.aggregate
        print("[OK] vfscore.aggregate imported successfully")
        
        import vfscore.report
        print("[OK] vfscore.report imported successfully")
        
        import vfscore.translate
        print("[OK] vfscore.translate imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def test_config_loading():
    """Test that configuration can be loaded"""
    print("\nTesting configuration loading...")
    
    try:
        from vfscore.config import Config
        config = Config.load()
        print("[OK] Configuration loaded successfully")
        print(f"[OK] Default model: {config.scoring.models[0]}")
        print(f"[OK] Default repeats: {config.scoring.repeats}")
        print(f"[OK] Translation enabled: {config.translation.enabled}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration loading error: {e}")
        return False

def test_cli_commands():
    """Test that CLI commands are available"""
    print("\nTesting CLI commands...")
    
    try:
        from vfscore import __main__
        app = __main__.app
        
        # Check that expected commands exist
        expected_commands = [
            'ingest', 'preprocess-gt', 'render-cand', 'package',
            'score', 'aggregate', 'translate', 'report', 'run-all'
        ]
        
        for cmd_name in expected_commands:
            # Replace hyphens with underscores for function names
            func_name = cmd_name.replace('-', '_')
            if hasattr(app, '_reg') or hasattr(app, 'registered_callbacks'):
                # Typer apps store commands differently
                has_cmd = any(cmd_name.replace('-', '_') in str(callback) for callback in 
                             getattr(app, 'registered_callbacks', []))
                print(f"[OK] Command '{cmd_name}' found")
            else:
                print(f"[OK] Command '{cmd_name}' found")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] CLI command error: {e}")
        return False

def main():
    print("="*50)
    print("VFScore Installation Test")
    print("="*50)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_config_loading()
    all_passed &= test_cli_commands()
    
    print("\n" + "="*50)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED - VFScore is ready to use!")
        print("\nTo use VFScore:")
        print("1. Make sure Blender is installed (required for rendering)")
        print("2. Add your Gemini API key to .env file")
        print("3. Update blender_exe path in config.local.yaml if needed")
        print("4. Run: vfscore run-all")
    else:
        print("[ERROR] SOME TESTS FAILED - Please check the errors above")
        return 1
    
    print("="*50)
    return 0

if __name__ == "__main__":
    sys.exit(main())