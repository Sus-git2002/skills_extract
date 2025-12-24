"""
Centralized Logging Configuration

Task: T1.5 - Setup Logging Framework

This module provides:
- Configurable logging to file and console
- Module-specific loggers
- Integration with pipeline configuration

Usage:
    from src.utils import setup_logging, get_logger
    
    # Setup logging (call once at startup)
    setup_logging(log_file="reports/pipeline.log", level="INFO")
    
    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Processing started")
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    level: str = "INFO",
    console: bool = True,
    log_format: Optional[str] = None
) -> None:
    """
    Configure logging for the pipeline.
    
    Args:
        log_file: Path to log file. None = no file logging.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to also log to console (stdout)
        log_format: Custom format string. None = use default format.
    
    Example:
        setup_logging(
            log_file="reports/pipeline.log",
            level="DEBUG",
            console=True
        )
    """
    # Default format if not specified
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers (prevents duplicate logs)
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name. Typically use __name__ for module-specific logging.
    
    Returns:
        Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing file: %s", filename)
        logger.debug("Detailed debug info: %s", data)
        logger.error("Something went wrong: %s", error)
    """
    return logging.getLogger(name)


def setup_logging_from_config(config) -> None:
    """
    Setup logging using a ConfigLoader instance.
    
    Args:
        config: ConfigLoader instance with logging settings
    
    Example:
        config = ConfigLoader.load("src/config/config.yaml")
        setup_logging_from_config(config)
    """
    setup_logging(
        log_file=config.get("logging.file"),
        level=config.get("logging.level", "INFO"),
        console=config.get("logging.console", True),
        log_format=config.get("logging.format")
    )


# =============================================================================
# Quick Test (run this file directly to test logging)
# =============================================================================
if __name__ == "__main__":
    # Test basic logging
    print("Testing logging setup...")
    
    setup_logging(level="DEBUG", console=True, log_file=None)
    
    logger = get_logger("test_module")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    print("\n✅ Logging test complete!")
