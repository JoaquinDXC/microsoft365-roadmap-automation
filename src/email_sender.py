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
    """Sends emails via SMTP (Office 365 compatible)."""

    def __init__(
        self,
        smtp_server: str = "smtp.office365.com",
        smtp_port: int = 587,
        from_address: str = config.EMAIL_FROM,
        password: str = config.EMAIL_PASSWORD,
    ):
        """
        Initialize SMTP email sender.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port (usually 587 for TLS)
            from_address: Sender email address
            password: Sender password (app password for Office 365)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_address = from_address
        self.password = password

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
        """Send email using SMTP with STARTTLS (Exchange Online compatible)."""
        try:
            # For port 587: connect without TLS, then STARTTLS
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                timeout=30,
                use_tls=False,  # Important: don't use TLS on connect for port 587
            ) as smtp:
                # Step 1: Initial greeting
                logger.debug(f"[SMTP] Connected to {self.smtp_server}:{self.smtp_port}")

                # Step 2: EHLO
                await smtp.ehlo()
                logger.debug("[SMTP] EHLO sent")

                # Step 3: STARTTLS (required for port 587)
                await smtp.starttls()
                logger.debug("[SMTP] STARTTLS initiated")

                # Step 4: EHLO after STARTTLS (Exchange Online requirement)
                await smtp.ehlo()
                logger.debug("[SMTP] EHLO sent after STARTTLS")

                # Step 5: Authenticate with app password
                await smtp.login(self.from_address, self.password)
                logger.debug(f"[SMTP] Authenticated as {self.from_address}")

                # Step 6: Send message
                await smtp.send_message(
                    MIMEText(message, "html"),
                    sender=self.from_address,
                    recipients=[to_address],
                )
                logger.info(f"[SMTP] Email sent to {to_address}")

                # Step 7: Proper connection close
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
    Send roadmap update email.

    Args:
        html_content: HTML content to send

    Returns:
        True if successful (or dry_run mode)
    """
    # Build email body
    email_body = f"""<div style="font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 850px; margin: auto; background-color: #ffffff; padding: 20px;">
    <div style="background-color: #0078d4; color: #ffffff; padding: 15px 25px; border-radius: 8px; margin-bottom: 25px; font-size: 22px; font-weight: bold; display: flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        Microsoft 365 Roadmap Update
    </div>
    {html_content}
</div>"""

    # Check for dry run mode
    if config.DRY_RUN:
        logger.info(f"DRY_RUN: Email would be sent to {config.EMAIL_TO}")
        logger.debug(f"Email subject: {config.EMAIL_SUBJECT}")
        logger.debug(f"Email body length: {len(email_body)} bytes")
        return True

    sender = SMTPEmailSender()
    return await sender.send(
        to_address=config.EMAIL_TO,
        subject=config.EMAIL_SUBJECT,
        body_html=email_body,
    )
