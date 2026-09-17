"""Configuration management - centralized settings and environment variables."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Import logger for debug logging during validation
try:
    from logger import logger
except ImportError:
    # Fallback if logger not available (e.g., early validation)
    import logging
    logger = logging.getLogger("config")


class ConfigError(Exception):
    """Configuration error."""
    pass


class Config:
    """Application configuration."""

    def __init__(self):
        """Load configuration from environment and .env file."""
        # Find .env in project root (not depending on working directory)
        env_path = self._find_env_file()
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()  # Fallback: search in current directory

        # NOW load environment variables (AFTER load_dotenv)
        self._load_env_vars()
        self._validate_env_vars()

    @staticmethod
    def _find_env_file() -> Optional[Path]:
        """
        Find .env file by searching up from this file's directory.

        Returns:
            Path to .env if found, None otherwise
        """
        # Start from directory of this config.py file
        current_dir = Path(__file__).parent.parent  # src/ -> project root

        # Look for .env in project root
        env_path = current_dir / ".env"
        if env_path.exists():
            return env_path

        # Fallback: look in current working directory
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            return cwd_env

        return None

    def _load_env_vars(self) -> None:
        """Load environment variables from .env file."""
        # Load after load_dotenv() has been called

        # DRY_RUN (load first as it affects other validations)
        self.DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

        # Email mode: none, smtp, graph
        self.EMAIL_MODE = os.getenv("EMAIL_MODE", "smtp").lower()

        # Email configuration (common to all modes)
        self.EMAIL_FROM = os.getenv("EMAIL_FROM", "")
        self.EMAIL_TO = os.getenv("EMAIL_TO", "")

        # SMTP configuration
        self.SMTP_HOST = os.getenv("SMTP_HOST", "")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

        # Legacy SMTP (for backward compatibility)
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

        # OAuth 2.0 configuration (for Microsoft Graph)
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
        self.OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
        self.OAUTH_TENANT_ID = os.getenv("OAUTH_TENANT_ID", "")
        self.OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost")

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def _validate_env_vars(self) -> None:
        """Validate required environment variables based on configuration mode."""
        # Validate EMAIL_MODE
        valid_modes = {"none", "smtp", "graph"}
        if self.EMAIL_MODE not in valid_modes:
            raise ConfigError(
                f"Invalid EMAIL_MODE: '{self.EMAIL_MODE}'. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        # DRY_RUN mode: minimal validation (only MCP and database need to work)
        if self.DRY_RUN:
            logger.debug("DRY_RUN=true: Skipping email configuration validation")
            return

        # Non-dry-run mode: validate email configuration
        common_required = ["EMAIL_FROM", "EMAIL_TO"]
        missing = [var for var in common_required if not getattr(self, var, "")]

        if missing:
            env_path = self._find_env_file()
            env_location = f"at {env_path}" if env_path else "in current directory"
            raise ConfigError(
                f"Missing required email variables: {', '.join(missing)}. "
                f"Please check your .env file {env_location}."
            )

        # Mode-specific validation
        if self.EMAIL_MODE == "none":
            logger.debug("EMAIL_MODE=none: Email sending disabled")
        elif self.EMAIL_MODE == "smtp":
            self._validate_smtp_config()
        elif self.EMAIL_MODE == "graph":
            self._validate_graph_config()

    def _validate_smtp_config(self) -> None:
        """Validate SMTP-specific configuration."""
        required_smtp = ["SMTP_HOST"]
        missing = [var for var in required_smtp if not getattr(self, var, "")]

        if missing:
            env_path = self._find_env_file()
            env_location = f"at {env_path}" if env_path else "in current directory"
            raise ConfigError(
                f"EMAIL_MODE=smtp but missing SMTP configuration: {', '.join(missing)}. "
                f"Please check your .env file {env_location}."
            )

        logger.debug(
            f"SMTP config: host={self.SMTP_HOST}, port={self.SMTP_PORT}, "
            f"use_tls={self.SMTP_USE_TLS}, auth={'yes' if self.SMTP_USERNAME else 'no'}"
        )

    def _validate_graph_config(self) -> None:
        """Validate Graph/OAuth-specific configuration."""
        # Try both naming conventions
        tenant_id = self.AZURE_TENANT_ID or self.OAUTH_TENANT_ID
        client_id = self.AZURE_CLIENT_ID or self.OAUTH_CLIENT_ID

        required_graph = {"tenant_id": tenant_id, "client_id": client_id}
        missing = [name for name, val in required_graph.items() if not val]

        if missing:
            env_path = self._find_env_file()
            env_location = f"at {env_path}" if env_path else "in current directory"
            raise ConfigError(
                f"EMAIL_MODE=graph but missing OAuth configuration: {', '.join(missing)}. "
                f"Please check your .env file {env_location}. "
                f"Use AZURE_TENANT_ID/AZURE_CLIENT_ID or OAUTH_TENANT_ID/OAUTH_CLIENT_ID."
            )

    # MRC MCP Configuration
    MCP_ENDPOINT: str = "https://www.microsoft.com/releasecommunications/mcp"
    MCP_TIMEOUT: int = 30

    # Roadmap filtering configuration
    RSS_MONTHS_BACK: int = 1  # Kept for backward compatibility

    # Allowed products for filtering
    ALLOWED_PRODUCTS: set[str] = {
        "Exchange Online",
        "Microsoft Teams",
        "SharePoint",
        "OneDrive",
    }

    # Email Configuration (SMTP - Microsoft 365 Exchange Online)
    EMAIL_SUBJECT: str = "Roadmap Microsoft 365 - Actualización Mensual"
    SMTP_SERVER: str = "smtp.office365.com"  # Microsoft 365 Exchange Online
    SMTP_PORT: int = 587  # STARTTLS port

    # Database
    DB_PATH: Path = Path("data/processed_items.db")

    # Logging
    LOG_DIR: Path = Path("logs")
    LOG_FILE: Path = LOG_DIR / "app.log"

    # HTTP Configuration
    HTTP_TIMEOUT: int = 30
    HTTP_RETRIES: int = 3
    HTTP_BACKOFF_FACTOR: float = 1.5

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
