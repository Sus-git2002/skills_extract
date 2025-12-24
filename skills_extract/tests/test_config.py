"""
Tests for Configuration Loader

Tests Task: T1.4 (Config Loader)
"""

import pytest
import yaml
from pathlib import Path

from src.config import ConfigLoader, ConfigurationError


class TestConfigLoader:
    """Test suite for ConfigLoader."""
    
    def test_load_valid_config(self, sample_config_yaml):
        """Test loading a valid configuration file."""
        config = ConfigLoader.load(sample_config_yaml)
        
        assert config is not None
        assert config.get("input.columns.text_column") == "description"
    
    def test_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load("nonexistent/config.yaml")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_invalid_yaml(self, tmp_path):
        """Test error on invalid YAML syntax."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(str(bad_yaml))
        
        assert "yaml" in str(exc_info.value).lower()
    
    def test_empty_config(self, tmp_path):
        """Test error on empty config file."""
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("")
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(str(empty_yaml))
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_missing_required_field(self, tmp_path):
        """Test validation catches missing required fields."""
        incomplete_config = {
            'input': {
                'file_path': 'data/test.csv'
                # Missing: columns.text_column
            },
            'output': {
                'directory': 'outputs'
            }
        }
        
        config_path = tmp_path / "incomplete.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(incomplete_config, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load(str(config_path))
        
        assert "text_column" in str(exc_info.value)
    
    def test_get_with_default(self, sample_config_yaml):
        """Test getting missing keys returns default value."""
        config = ConfigLoader.load(sample_config_yaml)
        
        # Key doesn't exist
        result = config.get("nonexistent.key", default="default_value")
        assert result == "default_value"
        
        # Key exists
        result = config.get("input.columns.text_column", default="fallback")
        assert result == "description"  # Not the default
    
    def test_get_nested_value(self, sample_config_yaml):
        """Test accessing deeply nested values."""
        config = ConfigLoader.load(sample_config_yaml)
        
        # Three levels deep
        text_col = config.get("input.columns.text_column")
        assert text_col == "description"
        
        # Two levels deep
        chunk_size = config.get("input.chunk_size")
        assert chunk_size == 1000
    
    def test_get_section(self, sample_config_yaml):
        """Test getting entire configuration sections."""
        config = ConfigLoader.load(sample_config_yaml)
        
        input_config = config.get_input_config()
        
        assert isinstance(input_config, dict)
        assert "file_path" in input_config
        assert "columns" in input_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
