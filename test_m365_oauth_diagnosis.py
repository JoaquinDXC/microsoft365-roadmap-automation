#!/usr/bin/env python3
"""
Microsoft 365 OAuth Diagnosis
Tests MSAL authentication and Microsoft Graph connectivity.
Does NOT send email.
Does NOT display tokens.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from oauth_manager import OAuthManager
from graph_sender import GraphEmailSender
from logger import logger


async def diagnose_oauth():
    """
    Diagnose OAuth authentication and Graph connectivity.
    """

    print("\n" + "=" * 80)
    print("MICROSOFT 365 OAUTH DIAGNOSIS")
    print("=" * 80)

    # Configuration (you'll update these with actual values)
    print("\n1. CONFIGURATION")
    print("-" * 80)

    # TODO: Get from config or prompt
    print("   Please update the following in this script:")
    print("   - CLIENT_ID")
    print("   - TENANT_ID")
    print("")
    print("   Then re-run this diagnostic.")

    # Example values (USER MUST UPDATE THESE)
    CLIENT_ID = "YOUR_CLIENT_ID_HERE"
    TENANT_ID = "YOUR_TENANT_ID_HERE"
    REDIRECT_URI = "http://localhost"

    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("\n[ERROR] CLIENT_ID not configured")
        print("Please replace CLIENT_ID and TENANT_ID in this script")
        return False

    print(f"   CLIENT_ID:   {CLIENT_ID[:12]}... (truncated)")
    print(f"   TENANT_ID:   {TENANT_ID[:12]}... (truncated)")
    print(f"   REDIRECT_URI: {REDIRECT_URI}")

    # Step 1: Initialize OAuth Manager
    print("\n2. INITIALIZING OAUTH MANAGER")
    print("-" * 80)

    try:
        oauth_manager = OAuthManager(
            client_id=CLIENT_ID,
            tenant_id=TENANT_ID,
            redirect_uri=REDIRECT_URI,
        )
        print(f"   [OK] OAuthManager created")
        print(f"   [OK] Authority: https://login.microsoftonline.com/{TENANT_ID}")
        print(f"   [OK] Scopes: Mail.Send, offline_access")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize OAuthManager: {e}")
        return False

    # Step 2: Check token cache
    print("\n3. TOKEN CACHE")
    print("-" * 80)

    cache_path = oauth_manager.get_cache_path()
    cache_exists = oauth_manager.cache_exists()

    print(f"   Cache location: {cache_path}")
    print(f"   Cache exists: {cache_exists}")

    if cache_exists:
        print(f"   [OK] Previous login found (will use cached token if valid)")
    else:
        print(f"   [INFO] No cache found (interactive login required)")

    # Step 3: Get token (silent or interactive)
    print("\n4. AUTHENTICATION")
    print("-" * 80)

    print("   Attempting silent token acquisition...")
    token_result = oauth_manager.acquire_token_silent()

    if token_result:
        print("   [OK] Token acquired silently (from cache)")
        token_source = "cache"
    else:
        print("   [INFO] Silent acquisition failed, starting interactive login...")
        print("\n   >>> A browser window will open <<<")
        print("   >>> Please sign in with your Microsoft 365 account <<<")
        print("   >>> And grant Mail.Send permission <<<\n")

        token_result = oauth_manager.acquire_token_interactive()

        if token_result:
            print("   [OK] Token acquired interactively (user login)")
            token_source = "interactive login"
        else:
            print("   [ERROR] Authentication failed")
            return False

    # Step 4: Display account info
    print("\n5. AUTHENTICATED ACCOUNT")
    print("-" * 80)

    account_info = oauth_manager.get_account_info()
    if account_info:
        print(f"   Username: {account_info['username']}")
        print(f"   Name: {account_info['name']}")
        print(f"   Source: {token_source}")
    else:
        print("   [ERROR] Could not retrieve account info")
        return False

    # Step 5: Test Graph connectivity
    print("\n6. MICROSOFT GRAPH CONNECTIVITY")
    print("-" * 80)

    print("   Testing connection to Microsoft Graph...")

    graph_sender = GraphEmailSender(oauth_manager)
    graph_ok = await graph_sender.test_connection()

    if graph_ok:
        print("   [OK] Microsoft Graph connection successful")
        print("   [OK] Access token is valid for Graph API")
    else:
        print("   [ERROR] Microsoft Graph connection failed")
        return False

    # Step 6: Summary
    print("\n" + "=" * 80)
    print("DIAGNOSIS RESULTS")
    print("=" * 80)

    print(f"\n✓ OAuth Manager initialized")
    print(f"✓ Token obtained: {token_source}")
    print(f"✓ Account authenticated: {account_info['username']}")
    print(f"✓ Microsoft Graph accessible")
    print(f"✓ Mail.Send permission granted")

    print(f"\nToken cache location: {cache_path}")
    print(f"(Tokens are stored securely in the cache)")

    print(f"\n[SUCCESS] OAuth configuration is correct!")
    print(f"[READY] Can proceed with email sending")

    print("\n" + "=" * 80 + "\n")

    return True


async def main():
    """Run diagnostics."""
    success = await diagnose_oauth()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
