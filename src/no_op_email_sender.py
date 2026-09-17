"""No-op email sender for dry-run and email_mode=none."""

from logger import logger


class NoOpEmailSender:
    """Email sender that does nothing (for DRY_RUN or EMAIL_MODE=none)."""

    async def send(self, to_address: str, subject: str, body_html: str) -> bool:
        """
        Simulate email send without actually sending.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body_html: HTML email body

        Returns:
            True (success)
        """
        logger.info(f"[NoOp] Email would be sent to {to_address}")
        logger.debug(f"[NoOp] Subject: {subject}")
        logger.debug(f"[NoOp] Body size: {len(body_html)} bytes")
        return True
