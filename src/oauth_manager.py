"""
Microsoft OAuth 2.0 Management using MSAL
Handles authentication, token caching, and token refresh for Microsoft Graph.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import msal
except ImportError:
    raise ImportError("msal package required: pip install msal")

from logger import logger


class OAuthManager:
    """Manages OAuth 2.0 authentication using MSAL PublicClientApplication."""

    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        redirect_uri: str = "http://localhost",
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize OAuth Manager.

        Args:
            client_id: Azure App Registration Client ID
            tenant_id: Azure Tenant ID
            redirect_uri: OAuth redirect URI (default: http://localhost)
            cache_dir: Directory for token cache (default: ~/.m365_roadmap)
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = [
            "https://graph.microsoft.com/.default",
            "offline_access",  # Required for refresh token
        ]

        # Token cache directory
        if cache_dir is None:
            cache_dir = str(Path.home() / ".m365_roadmap")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "token_cache.json"

        # Initialize MSAL app
        self.app = self._create_app()

        logger.debug(f"OAuthManager initialized: {self.client_id}")
        logger.debug(f"Token cache: {self.cache_file}")

    def _create_app(self) -> msal.PublicClientApplication:
        """Create MSAL PublicClientApplication with persistent token cache."""
        cache = self._load_cache()

        app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=cache,
        )

        return app

    def _load_cache(self) -> msal.TokenCache:
        """Load token cache from disk, or create new if doesn't exist."""
        cache = msal.TokenCache()

        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache.deserialize(f.read())
                logger.debug(f"Token cache loaded from {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")
                logger.debug("Using new (empty) token cache")
        else:
            logger.debug("Token cache not found, using new empty cache")

        return cache

    def _save_cache(self) -> None:
        """Save token cache to disk."""
        try:
            if self.app.token_cache.has_state_changed:
                with open(self.cache_file, "w") as f:
                    f.write(self.app.token_cache.serialize())
                # Protect file: only owner can read/write
                self.cache_file.chmod(0o600)
                logger.debug(f"Token cache saved to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")

    def acquire_token_silent(self) -> Optional[Dict[str, Any]]:
        """
        Acquire token silently using cached credentials.

        Returns:
            Token dict with access_token, or None if not available
        """
        accounts = self.app.get_accounts()

        if not accounts:
            logger.debug("No cached account found")
            return None

        account = accounts[0]
        logger.debug(f"Using cached account: {account.get('username', 'unknown')}")

        token_result = self.app.acquire_token_silent(
            scopes=self.scopes,
            account=account,
        )

        if token_result and "access_token" in token_result:
            logger.debug("Token acquired silently (from cache or refresh)")
            self._save_cache()
            return token_result
        else:
            logger.debug("Silent token acquisition failed, interactive login required")
            return None

    def acquire_token_interactive(self) -> Optional[Dict[str, Any]]:
        """
        Acquire token interactively (opens browser for user login).

        Returns:
            Token dict with access_token, or None if failed
        """
        logger.info("Initiating interactive login...")
        logger.info("A browser window will open for you to sign in")

        token_result = self.app.acquire_token_by_auth_code_flow(
            flow={
                "client_id": self.client_id,
                "authority": self.authority,
                "scopes": self.scopes,
                "redirect_uri": self.redirect_uri,
            }
        )

        if token_result and "access_token" in token_result:
            logger.info("Interactive authentication successful")
            self._save_cache()
            return token_result
        else:
            error = token_result.get("error_description", "Unknown error")
            logger.error(f"Interactive authentication failed: {error}")
            return None

    def get_token(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get valid access token, using cache or interactive login as needed.

        Args:
            force_refresh: If True, ignore cache and force interactive login

        Returns:
            Token dict with access_token, or None if failed
        """
        if force_refresh:
            logger.info("Forcing interactive re-authentication...")
            return self.acquire_token_interactive()

        # Try silent first
        token = self.acquire_token_silent()
        if token:
            return token

        # Fall back to interactive
        return self.acquire_token_interactive()

    def get_account_info(self) -> Optional[Dict[str, str]]:
        """
        Get information about authenticated account.

        Returns:
            Dict with username, tenant, or None if no account
        """
        accounts = self.app.get_accounts()

        if not accounts:
            return None

        account = accounts[0]
        return {
            "username": account.get("username", "unknown"),
            "name": account.get("name", "unknown"),
            "home_account_id": account.get("home_account_id", "unknown"),
        }

    def clear_cache(self) -> None:
        """Clear token cache (for logout or troubleshooting)."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info(f"Token cache cleared: {self.cache_file}")
            else:
                logger.debug("No token cache to clear")
        except Exception as e:
            logger.error(f"Failed to clear token cache: {e}")

    def get_cache_path(self) -> str:
        """Get path to token cache file."""
        return str(self.cache_file)

    def cache_exists(self) -> bool:
        """Check if token cache exists."""
        return self.cache_file.exists()
