"""
Skills Extraction Pipeline

A production-grade, dataset-agnostic pipeline for extracting skills 
from job descriptions.

Modules:
    - config: Configuration management
    - data: Input/output handling
    - features: Preprocessing and extraction logic
    - models: ML-based extraction (future)
    - visualization: Analytics and reporting
    - utils: Utility functions
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from src.config.config_loader import ConfigLoader, ConfigurationError
from src.utils.logger import setup_logging, get_logger

__all__ = [
    "ConfigLoader",
    "ConfigurationError", 
    "setup_logging",
    "get_logger",
]
