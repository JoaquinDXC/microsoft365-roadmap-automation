"""Factory for creating appropriate email sender based on configuration."""

from typing import Union
from config import config, ConfigError
from logger import logger


def create_email_sender() -> Union["NoOpEmailSender", "SMTPEmailSender", "GraphEmailSender"]:
    """
    Create appropriate email sender based on configuration.

    Returns:
        Email sender instance (NoOp, SMTP, or Graph)

    Raises:
        ConfigError if configuration is invalid
    """
    # DRY_RUN mode: always use no-op sender
    if config.DRY_RUN:
        logger.info("Creating NoOp email sender (DRY_RUN=true)")
        from no_op_email_sender import NoOpEmailSender
        return NoOpEmailSender()

    # Select based on EMAIL_MODE
    if config.EMAIL_MODE == "none":
        logger.info("Creating NoOp email sender (EMAIL_MODE=none)")
        from no_op_email_sender import NoOpEmailSender
        return NoOpEmailSender()

    elif config.EMAIL_MODE == "smtp":
        logger.info("Creating SMTP email sender")
        from email_sender import SMTPEmailSender

        # Determine SMTP credentials
        smtp_username = config.SMTP_USERNAME
        smtp_password = config.SMTP_PASSWORD

        # Fallback to legacy EMAIL_PASSWORD for backward compatibility
        if not smtp_password and config.EMAIL_PASSWORD:
            smtp_password = config.EMAIL_PASSWORD

        return SMTPEmailSender(
            smtp_server=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            from_address=config.EMAIL_FROM,
            username=smtp_username if smtp_username else None,
            password=smtp_password if smtp_password else None,
            use_tls=config.SMTP_USE_TLS,
        )

    elif config.EMAIL_MODE == "graph":
        logger.info("Creating Microsoft Graph email sender")
        from graph_sender import GraphEmailSender
        from oauth_manager import OAuthManager

        # Use either naming convention
        tenant_id = config.AZURE_TENANT_ID or config.OAUTH_TENANT_ID
        client_id = config.AZURE_CLIENT_ID or config.OAUTH_CLIENT_ID

        oauth_manager = OAuthManager(
            client_id=client_id,
            tenant_id=tenant_id,
            redirect_uri=config.OAUTH_REDIRECT_URI,
        )

        return GraphEmailSender(oauth_manager=oauth_manager)

    else:
        raise ConfigError(f"Invalid EMAIL_MODE: {config.EMAIL_MODE}")
