#!/usr/bin/env python3
"""
Quick configuration test utility.
Validates all required environment variables before running the main automation.
"""

import sys
import os
from pathlib import Path

# Ensure we're in the project root
project_root = Path(__file__).parent
os.chdir(project_root)

sys.path.insert(0, str(project_root / "src"))

from config import config, ConfigError
from logger import logger


def test_configuration() -> bool:
    """
    Test that all configuration is correct.

    Returns:
        True if all checks pass
    """
    print("\n" + "=" * 60)
    print("M365 Roadmap Automation - Configuration Test")
    print("=" * 60 + "\n")

    all_pass = True

    # Test 1: Required environment variables
    print("[TEST] Required environment variables...")
    required_vars = {
        "GEMINI_API_KEY": config.GEMINI_API_KEY,
        "EMAIL_FROM": config.EMAIL_FROM,
        "EMAIL_PASSWORD": config.EMAIL_PASSWORD,
        "EMAIL_TO": config.EMAIL_TO,
    }

    for var_name, var_value in required_vars.items():
        if var_value and str(var_value).strip():
            status = "[OK]"
            value_preview = str(var_value)[:20] + "..." if len(str(var_value)) > 20 else str(var_value)
            print(f"  {status} {var_name}: {value_preview}")
        else:
            print(f"  [FAIL] {var_name}: NOT SET or EMPTY")
            all_pass = False

    # Test 2: Directories
    print("\n[TEST] Directories...")
    config.ensure_directories()
    print(f"  [OK] Data directory: {config.DB_PATH.parent}")
    print(f"  [OK] Logs directory: {config.LOG_DIR}")

    # Test 3: Configuration values
    print("\n[TEST] Configuration values...")
    print(f"  [OK] RSS URL: {config.RSS_URL}")
    print(f"  [OK] RSS Max Results: {config.RSS_MAX_RESULTS}")
    print(f"  [OK] RSS Months Back: {config.RSS_MONTHS_BACK}")
    print(f"  [OK] Gemini Model: {config.GEMINI_MODEL}")
    print(f"  [OK] Allowed Products: {', '.join(config.ALLOWED_PRODUCTS)}")
    print(f"  [OK] Email From: {config.EMAIL_FROM}")
    print(f"  [OK] Log Level: {config.LOG_LEVEL}")

    # Test 4: Database
    print("\n[TEST] Database...")
    try:
        from database import ProcessedItemsDB
        db = ProcessedItemsDB()
        stats = db.get_stats()
        print(f"  [OK] Database initialized at {config.DB_PATH}")
        print(f"  [OK] Total processed items: {stats.get('total', 0)}")
    except Exception as e:
        print(f"  [FAIL] Database error: {e}")
        all_pass = False

    # Test 5: Logger
    print("\n[TEST] Logger...")
    logger.info("Test message")
    print(f"  [OK] Logger initialized")
    print(f"  [OK] Log file: {config.LOG_FILE}")

    # Summary
    print("\n" + "=" * 60)
    if all_pass:
        print("[OK] ALL CONFIGURATION TESTS PASSED")
        print("\nYou can now run: python main.py")
    else:
        print("[FAIL] CONFIGURATION ISSUES FOUND")
        print("\nPlease fix the issues above and try again.")
        print("See SETUP.md for detailed instructions.")

    print("=" * 60 + "\n")

    return all_pass


if __name__ == "__main__":
    try:
        success = test_configuration()
        sys.exit(0 if success else 1)
    except ConfigError as e:
        print(f"\n✗ Configuration Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}\n")
        sys.exit(1)
