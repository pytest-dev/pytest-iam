import logging

logger = logging.getLogger("tests.logging")


def test_existing_loggers_are_not_disabled(iam_server):
    """Starting the IAM server keeps the loggers of the tested project enabled."""
    assert not logger.disabled


def test_root_logger_is_not_configured(iam_server):
    """Starting the IAM server leaves the root logger untouched."""
    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert "canaille" not in [handler.name for handler in root.handlers]
