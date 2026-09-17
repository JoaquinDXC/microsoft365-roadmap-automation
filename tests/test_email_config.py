#!/usr/bin/env python3
"""Tests for email configuration and sender selection."""

import os
import sys
from pathlib import Path
from unittest import mock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestConfigValidation:
    """Test configuration validation with different modes."""

    def test_dry_run_skips_email_validation(self):
        """DRY_RUN=true should skip email configuration validation."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "true",
            "EMAIL_MODE": "none",
            # Intentionally missing EMAIL_FROM, EMAIL_TO, SMTP_HOST
        }):
            # Reload config to pick up mocked environment
            import importlib
            import config as config_module
            importlib.reload(config_module)

            # Should not raise ConfigError
            assert config_module.config.DRY_RUN is True
            assert config_module.config.EMAIL_MODE == "none"

    def test_dry_run_with_missing_smtp_config(self):
        """DRY_RUN=true should work without SMTP configuration."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "true",
            "EMAIL_MODE": "smtp",
        }):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            assert config_module.config.DRY_RUN is True

    def test_smtp_mode_requires_host(self):
        """EMAIL_MODE=smtp and DRY_RUN=false should require SMTP_HOST."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "smtp",
            "EMAIL_FROM": "sender@test.com",
            "EMAIL_TO": "recipient@test.com",
            # Missing SMTP_HOST
        }, clear=False):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from config import ConfigError
            with pytest.raises(ConfigError, match="SMTP_HOST"):
                config_module.Config()

    def test_smtp_relay_without_auth(self):
        """SMTP Relay without authentication should be valid."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "smtp",
            "EMAIL_FROM": "roadmap@test.com",
            "EMAIL_TO": "recipient@test.com",
            "SMTP_HOST": "exchange-relay.local",
            "SMTP_PORT": "25",
            "SMTP_USE_TLS": "false",
            # No SMTP_USERNAME/PASSWORD
        }, clear=False):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            assert config_module.config.SMTP_HOST == "exchange-relay.local"
            assert config_module.config.SMTP_PORT == 25
            assert config_module.config.SMTP_USE_TLS is False

    def test_graph_mode_requires_tenant_and_client_id(self):
        """EMAIL_MODE=graph should require tenant and client IDs."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "graph",
            "EMAIL_FROM": "sender@test.com",
            "EMAIL_TO": "recipient@test.com",
            # Missing AZURE_TENANT_ID and AZURE_CLIENT_ID
        }, clear=False):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from config import ConfigError
            with pytest.raises(ConfigError, match="tenant_id.*client_id"):
                config_module.Config()

    def test_invalid_email_mode(self):
        """Invalid EMAIL_MODE should raise ConfigError."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "invalid_mode",
        }, clear=False):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from config import ConfigError
            with pytest.raises(ConfigError, match="Invalid EMAIL_MODE"):
                config_module.Config()


class TestEmailFactory:
    """Test email sender factory."""

    def test_factory_creates_noop_for_dry_run(self):
        """Factory should create NoOp sender for DRY_RUN=true."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "true",
            "EMAIL_MODE": "smtp",
        }):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from email_factory import create_email_sender
            from no_op_email_sender import NoOpEmailSender

            sender = create_email_sender()
            assert isinstance(sender, NoOpEmailSender)

    def test_factory_creates_noop_for_none_mode(self):
        """Factory should create NoOp sender for EMAIL_MODE=none."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "none",
            "EMAIL_FROM": "sender@test.com",
            "EMAIL_TO": "recipient@test.com",
        }):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from email_factory import create_email_sender
            from no_op_email_sender import NoOpEmailSender

            sender = create_email_sender()
            assert isinstance(sender, NoOpEmailSender)

    def test_factory_creates_smtp_sender(self):
        """Factory should create SMTP sender for EMAIL_MODE=smtp."""
        with mock.patch.dict(os.environ, {
            "DRY_RUN": "false",
            "EMAIL_MODE": "smtp",
            "EMAIL_FROM": "sender@test.com",
            "EMAIL_TO": "recipient@test.com",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USE_TLS": "true",
            "SMTP_USERNAME": "user",
            "SMTP_PASSWORD": "pass",
        }):
            import importlib
            import config as config_module
            importlib.reload(config_module)

            from email_factory import create_email_sender
            from email_sender import SMTPEmailSender

            sender = create_email_sender()
            assert isinstance(sender, SMTPEmailSender)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
