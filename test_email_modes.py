#!/usr/bin/env python3
"""Simple test to verify email configuration modes work correctly."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_dry_run_no_credentials():
    """Test 1: DRY_RUN=true should not require email credentials."""
    print("\n" + "=" * 70)
    print("TEST 1: DRY_RUN=true (should not require email credentials)")
    print("=" * 70)

    # Set minimal environment
    test_env = {
        "DRY_RUN": "true",
        "EMAIL_MODE": "none",
    }

    # Mock environment
    for key, value in test_env.items():
        os.environ[key] = value

    # Remove email config
    for key in ["EMAIL_FROM", "EMAIL_TO", "EMAIL_PASSWORD", "SMTP_HOST",
                "AZURE_TENANT_ID", "AZURE_CLIENT_ID"]:
        os.environ.pop(key, None)

    try:
        # Reload config
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        else:
            import config

        print("✅ Config loaded successfully without email credentials")
        print(f"   DRY_RUN={os.environ.get('DRY_RUN')}")
        print(f"   EMAIL_MODE={os.environ.get('EMAIL_MODE')}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_smtp_relay_no_auth():
    """Test 2: SMTP Relay without authentication should be valid."""
    print("\n" + "=" * 70)
    print("TEST 2: SMTP Relay (no authentication)")
    print("=" * 70)

    test_env = {
        "DRY_RUN": "false",
        "EMAIL_MODE": "smtp",
        "EMAIL_FROM": "roadmap@test.com",
        "EMAIL_TO": "recipient@test.com",
        "SMTP_HOST": "mail.test.local",
        "SMTP_PORT": "25",
        "SMTP_USE_TLS": "false",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    # Remove auth
    for key in ["SMTP_USERNAME", "SMTP_PASSWORD"]:
        os.environ.pop(key, None)

    try:
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        else:
            import config

        print("✅ Config loaded successfully for SMTP relay")
        print(f"   SMTP_HOST={os.environ.get('SMTP_HOST')}")
        print(f"   SMTP_PORT={os.environ.get('SMTP_PORT')}")
        print(f"   SMTP_USE_TLS={os.environ.get('SMTP_USE_TLS')}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_email_factory_noop():
    """Test 3: Factory creates NoOp sender for DRY_RUN."""
    print("\n" + "=" * 70)
    print("TEST 3: Email Factory creates NoOp for DRY_RUN")
    print("=" * 70)

    test_env = {
        "DRY_RUN": "true",
        "EMAIL_MODE": "smtp",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    try:
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        if 'email_factory' in sys.modules:
            importlib.reload(sys.modules['email_factory'])

        from email_factory import create_email_sender
        from no_op_email_sender import NoOpEmailSender

        sender = create_email_sender()

        if isinstance(sender, NoOpEmailSender):
            print("✅ Factory correctly created NoOpEmailSender")
            return True
        else:
            print(f"❌ Factory created {type(sender).__name__} instead of NoOpEmailSender")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test 4: Config validates EMAIL_MODE values."""
    print("\n" + "=" * 70)
    print("TEST 4: Config validates EMAIL_MODE")
    print("=" * 70)

    test_env = {
        "DRY_RUN": "false",
        "EMAIL_MODE": "invalid_mode",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    try:
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])

        print("❌ Should have raised ConfigError for invalid EMAIL_MODE")
        return False
    except Exception as e:
        if "Invalid EMAIL_MODE" in str(e):
            print(f"✅ Correctly rejected invalid EMAIL_MODE: {e}")
            return True
        else:
            print(f"❌ Wrong error: {e}")
            return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("EMAIL CONFIGURATION TESTS")
    print("=" * 70)

    results = []

    try:
        results.append(("DRY_RUN=true (no credentials)", test_dry_run_no_credentials()))
    except Exception as e:
        print(f"Test 1 failed with exception: {e}")
        results.append(("DRY_RUN=true (no credentials)", False))

    try:
        results.append(("SMTP Relay (no auth)", test_smtp_relay_no_auth()))
    except Exception as e:
        print(f"Test 2 failed with exception: {e}")
        results.append(("SMTP Relay (no auth)", False))

    try:
        results.append(("Factory creates NoOp", test_email_factory_noop()))
    except Exception as e:
        print(f"Test 3 failed with exception: {e}")
        results.append(("Factory creates NoOp", False))

    try:
        results.append(("Config validates EMAIL_MODE", test_config_validation()))
    except Exception as e:
        print(f"Test 4 failed with exception: {e}")
        results.append(("Config validates EMAIL_MODE", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    sys.exit(0 if passed == total else 1)
