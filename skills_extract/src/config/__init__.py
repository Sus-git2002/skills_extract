"""Configuration management for the skills extraction pipeline."""

from .config_loader import ConfigLoader, ConfigurationError

__all__ = ["ConfigLoader", "ConfigurationError"]
