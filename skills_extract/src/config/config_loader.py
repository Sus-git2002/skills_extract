"""
Configuration Loader with Validation

Task: T1.4 - Create Config Loader

This module provides:
- YAML configuration loading
- Required field validation
- Safe nested key access with dot notation
- Clear error messages for missing/invalid config

Usage:
    from src.config import ConfigLoader, ConfigurationError
    
    # Load and validate config
    config = ConfigLoader.load("src/config/config.yaml")
    
    # Access values with dot notation
    text_column = config.get("input.columns.text_column")
    log_level = config.get("logging.level", default="INFO")
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigurationError(Exception):
    """
    Raised when configuration is invalid or missing required fields.
    
    Provides clear error messages to help users fix config issues.
    """
    pass


class ConfigLoader:
    """
    Load and validate pipeline configuration from YAML files.
    
    Features:
    - Validates all required fields are present
    - Provides dot-notation access to nested values
    - Returns sensible defaults for optional fields
    - Gives helpful error messages
    
    Example:
        # Load config
        config = ConfigLoader.load("src/config/config.yaml")
        
        # Access nested values
        file_path = config.get("input.file_path")
        chunk_size = config.get("input.chunk_size", default=5000)
        
        # Access entire sections
        input_config = config.get_input_config()
    """
    
    # Required fields that MUST exist in configuration
    REQUIRED_FIELDS: List[str] = [
        "input.file_path",
        "input.columns.text_column",
        "extraction.dictionaries.technical",
        "output.directory",
    ]
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize with a configuration dictionary.
        
        Args:
            config_dict: Parsed YAML configuration
        
        Note: Use ConfigLoader.load() instead of calling this directly.
        """
        self._config = config_dict
    
    @classmethod
    def load(cls, config_path: str) -> "ConfigLoader":
        """
        Load and validate configuration from a YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        
        Returns:
            ConfigLoader instance with validated configuration
        
        Raises:
            ConfigurationError: If file not found, invalid YAML, or missing required fields
        
        Example:
            config = ConfigLoader.load("src/config/config.yaml")
        """
        path = Path(config_path)
        
        # Check file exists
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}\n"
                f"Please create the config file or check the path."
            )
        
        # Load YAML
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in {config_path}:\n{e}"
            )
        
        if config_dict is None:
            raise ConfigurationError(
                f"Configuration file is empty: {config_path}"
            )
        
        # Create instance and validate
        instance = cls(config_dict)
        instance.validate()
        
        return instance
    
    def validate(self) -> None:
        """
        Validate all required configuration fields are present.
        
        Raises:
            ConfigurationError: If any required field is missing
        """
        missing_fields = []
        
        for field_path in self.REQUIRED_FIELDS:
            value = self.get(field_path)
            if value is None:
                missing_fields.append(field_path)
        
        if missing_fields:
            field_list = "\n  - ".join(missing_fields)
            raise ConfigurationError(
                f"Missing required configuration fields:\n  - {field_list}\n\n"
                f"Please add these fields to your config.yaml file."
            )
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation for nested keys.
        
        Args:
            key_path: Dot-separated path to the value (e.g., "input.columns.text_column")
            default: Value to return if key doesn't exist
        
        Returns:
            Configuration value or default
        
        Examples:
            config.get("input.file_path")
            config.get("input.chunk_size", default=5000)
            config.get("analytics.enabled", default=False)
        """
        keys = key_path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_input_config(self) -> Dict[str, Any]:
        """Get the entire input configuration section."""
        return self._config.get("input", {})
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """Get the entire preprocessing configuration section."""
        return self._config.get("preprocessing", {})
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Get the entire extraction configuration section."""
        return self._config.get("extraction", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get the entire output configuration section."""
        return self._config.get("output", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get the entire logging configuration section."""
        return self._config.get("logging", {})
    
    def get_analytics_config(self) -> Dict[str, Any]:
        """Get the entire analytics configuration section (Phase 2)."""
        return self._config.get("analytics", {})
    
    def get_rules_config(self) -> Dict[str, Any]:
        """Get the entire rules configuration section (Phase 2)."""
        return self._config.get("rules", {})
    
    @property
    def raw(self) -> Dict[str, Any]:
        """
        Access the raw configuration dictionary.
        
        Use this only when you need direct access to the full config.
        Prefer using get() for accessing specific values.
        """
        return self._config
    
    def __repr__(self) -> str:
        """String representation showing key config values."""
        return (
            f"ConfigLoader(\n"
            f"  input_file='{self.get('input.file_path')}',\n"
            f"  text_column='{self.get('input.columns.text_column')}',\n"
            f"  output_dir='{self.get('output.directory')}'\n"
            f")"
        )


# =============================================================================
# Quick Test (run this file directly to test config loading)
# =============================================================================
if __name__ == "__main__":
    import sys
    
    print("Testing ConfigLoader...")
    print("=" * 50)
    
    # Try to load config
    config_path = "src/config/config.yaml"
    
    try:
        config = ConfigLoader.load(config_path)
        print(f"✅ Successfully loaded: {config_path}")
        print()
        print("Configuration summary:")
        print(config)
        print()
        print("Sample values:")
        print(f"  - Input file: {config.get('input.file_path')}")
        print(f"  - Text column: {config.get('input.columns.text_column')}")
        print(f"  - Log level: {config.get('logging.level')}")
        print(f"  - Output dir: {config.get('output.directory')}")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error:\n{e}")
        sys.exit(1)
    
    print()
    print("✅ ConfigLoader test complete!")
