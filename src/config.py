"""Configuration management - centralized settings and environment variables."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


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

        # Email configuration
        self.EMAIL_FROM = os.getenv("EMAIL_FROM", "")
        self.EMAIL_TO = os.getenv("EMAIL_TO", "")

        # Legacy SMTP (for backward compatibility, optional)
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

        # OAuth 2.0 configuration (for Microsoft Graph)
        self.OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
        self.OAUTH_TENANT_ID = os.getenv("OAUTH_TENANT_ID", "")
        self.OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost")

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

    def _validate_env_vars(self) -> None:
        """Validate required environment variables."""
        required = ["EMAIL_TO", "EMAIL_FROM", "EMAIL_PASSWORD"]

        missing = [var for var in required if not getattr(self, var, "")]
        if missing:
            env_path = self._find_env_file()
            env_location = f"at {env_path}" if env_path else "in current directory"
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please check your .env file {env_location} and ensure these variables are set."
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
