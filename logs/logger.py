"""
Logging Configuration for AI Terminal
====================================
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logger with file and console handlers"""

    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_file = logs_dir / 'ai_terminal.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler
    error_log_file = logs_dir / 'ai_terminal_errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_log_files():
    """Get list of log files"""
    logs_dir = Path('logs')
    if logs_dir.exists():
        return [f for f in logs_dir.iterdir() if f.suffix == '.log']
    return []


def clear_logs():
    """Clear all log files"""
    logs_dir = Path('logs')
    if logs_dir.exists():
        for log_file in logs_dir.glob('*.log*'):
            try:
                log_file.unlink()
            except Exception as e:
                print(f"Error deleting {log_file}: {e}")


if __name__ == "__main__":
    # Test logging
    test_logger = setup_logger("test")
    test_logger.info("Test info message")
    test_logger.warning("Test warning message")
    test_logger.error("Test error message")