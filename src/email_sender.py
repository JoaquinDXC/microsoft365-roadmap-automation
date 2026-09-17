"""Email sending via SMTP (Office 365)."""

import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import Optional

from config import config
from logger import logger


class SMTPEmailSender:
    """Sends emails via SMTP (Office 365 compatible, or on-premises relay)."""

    def __init__(
        self,
        smtp_server: str = "smtp.office365.com",
        smtp_port: int = 587,
        from_address: str = config.EMAIL_FROM,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
    ):
        """
        Initialize SMTP email sender.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port (usually 587 for TLS, 25/465 for relay)
            from_address: Sender email address
            username: SMTP username (optional for relay without auth)
            password: SMTP password (optional for relay without auth)
            use_tls: Whether to use STARTTLS (True) or SSL (False)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_address = from_address
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send(
        self,
        to_address: str,
        subject: str,
        body_html: str,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body_html: HTML email body

        Returns:
            True if successful
        """
        try:
            logger.info(f"Sending email to {to_address}")

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = to_address

            # Attach HTML
            html_part = MIMEText(body_html, "html")
            msg.attach(html_part)

            # Send via SMTP
            success = await self._send_via_smtp(to_address, msg.as_string())

            if success:
                logger.info(f"Email sent successfully to {to_address}")
            else:
                logger.error(f"Failed to send email to {to_address}")

            return success

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    async def _send_via_smtp(self, to_address: str, message: str) -> bool:
        """Send email using SMTP (STARTTLS, SSL, or plain relay)."""
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                timeout=30,
                use_tls=False,  # Don't use TLS on connect; handle it manually
            ) as smtp:
                logger.debug(f"[SMTP] Connected to {self.smtp_server}:{self.smtp_port}")

                # Step 1: EHLO
                await smtp.ehlo()
                logger.debug("[SMTP] EHLO sent")

                # Step 2: STARTTLS if enabled
                if self.use_tls:
                    await smtp.starttls()
                    logger.debug("[SMTP] STARTTLS initiated")

                    # EHLO after STARTTLS (required for some servers)
                    await smtp.ehlo()
                    logger.debug("[SMTP] EHLO sent after STARTTLS")

                # Step 3: Authenticate if credentials provided
                if self.username and self.password:
                    await smtp.login(self.username, self.password)
                    logger.debug(f"[SMTP] Authenticated as {self.username}")
                else:
                    logger.debug("[SMTP] No authentication (relay mode)")

                # Step 4: Send message
                await smtp.send_message(
                    MIMEText(message, "html"),
                    sender=self.from_address,
                    recipients=[to_address],
                )
                logger.info(f"[SMTP] Email sent to {to_address}")

                # Step 5: Close connection
                await smtp.quit()
                logger.debug("[SMTP] Connection closed")

                return True

        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False


async def send_roadmap_email(html_content: str) -> bool:
    """
    Send roadmap update email using configured email sender.

    Args:
        html_content: HTML content to send

    Returns:
        True if successful (or no-op sender)
    """
    from email_factory import create_email_sender

    # Build email body
    email_body = f"""<div style="font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: auto; background-color: #ffffff; padding: 20px;">
    <div style="background-color: #0078d4; color: #ffffff; padding: 15px 25px; border-radius: 8px; margin-bottom: 25px; font-size: 22px; font-weight: bold; display: flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        Microsoft 365 Roadmap Update
    </div>
    {html_content}
</div>"""

    # Create appropriate sender based on configuration
    sender = create_email_sender()

    return await sender.send(
        to_address=config.EMAIL_TO,
        subject=config.EMAIL_SUBJECT,
        body_html=email_body,
    )
