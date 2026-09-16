"""
Microsoft Graph Email Sender
Sends emails using Microsoft Graph API with OAuth 2.0 token.
"""

import asyncio
import json
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from base64 import b64encode

try:
    import aiohttp
except ImportError:
    raise ImportError("aiohttp package required: pip install aiohttp")

from logger import logger
from oauth_manager import OAuthManager


class GraphEmailSender:
    """Sends emails using Microsoft Graph API (/me/sendMail)."""

    def __init__(self, oauth_manager: OAuthManager):
        """
        Initialize Graph Email Sender.

        Args:
            oauth_manager: OAuthManager instance with valid token
        """
        self.oauth_manager = oauth_manager
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.send_mail_url = f"{self.graph_endpoint}/me/sendMail"

    async def send_email(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        cc: Optional[list] = None,
        bcc: Optional[list] = None,
    ) -> bool:
        """
        Send email via Microsoft Graph API.

        Args:
            to_address: Recipient email address
            subject: Email subject
            html_body: HTML email body
            cc: List of CC email addresses
            bcc: List of BCC email addresses

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get valid token
            token_result = self.oauth_manager.get_token()
            if not token_result or "access_token" not in token_result:
                logger.error("Failed to get access token")
                return False

            access_token = token_result["access_token"]

            # Build email message
            message = self._build_message(
                to_address=to_address,
                subject=subject,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
            )

            # Send via Graph API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "message": message,
                    "saveToSentItems": True,
                }

                logger.debug(f"Sending email to {to_address} via Microsoft Graph")

                async with session.post(
                    self.send_mail_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 202:
                        logger.info(f"Email sent to {to_address}")
                        return True
                    elif response.status == 401:
                        logger.error("Authentication failed (401)")
                        return False
                    elif response.status == 403:
                        logger.error("Permission denied (403) - Mail.Send permission required")
                        return False
                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"Bad request (400): {error_text}")
                        return False
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Graph API error ({response.status}): {error_text}"
                        )
                        return False

        except asyncio.TimeoutError:
            logger.error("Email send timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _build_message(
        self,
        to_address: str,
        subject: str,
        html_body: str,
        cc: Optional[list] = None,
        bcc: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Build Microsoft Graph message object.

        Args:
            to_address: Recipient
            subject: Subject line
            html_body: HTML body content
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Message dict for Graph API
        """
        to_recipients = [{"emailAddress": {"address": to_address}}]

        cc_recipients = []
        if cc:
            cc_recipients = [{"emailAddress": {"address": addr}} for addr in cc]

        bcc_recipients = []
        if bcc:
            bcc_recipients = [{"emailAddress": {"address": addr}} for addr in bcc]

        message = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": to_recipients,
        }

        if cc_recipients:
            message["ccRecipients"] = cc_recipients

        if bcc_recipients:
            message["bccRecipients"] = bcc_recipients

        return message

    async def test_connection(self) -> bool:
        """
        Test Graph API connection by fetching user info.

        Returns:
            True if connection successful
        """
        try:
            token_result = self.oauth_manager.get_token()
            if not token_result or "access_token" not in token_result:
                logger.error("Failed to get access token")
                return False

            access_token = token_result["access_token"]

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                }

                # Get /me info
                async with session.get(
                    f"{self.graph_endpoint}/me",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        logger.info(f"Graph connection successful")
                        logger.debug(f"User: {user_info.get('userPrincipalName', 'unknown')}")
                        return True
                    else:
                        logger.error(f"Graph API error ({response.status})")
                        return False

        except Exception as e:
            logger.error(f"Graph connection test failed: {e}")
            return False
