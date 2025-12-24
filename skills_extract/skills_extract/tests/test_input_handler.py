"""
Tests for Input Handler

Tests Tasks: T2.1 - T2.6
"""

import pytest
import pandas as pd
from pathlib import Path

from src.data import InputHandler, InputError
from tests.conftest import MockConfig


class TestInputHandler:
    """Test suite for InputHandler."""
    
    def test_load_csv(self, sample_csv, mock_config_dict):
        """Test loading CSV file."""
        mock_config_dict['input']['file_path'] = sample_csv
        mock_config_dict['input']['columns']['text_column'] = 'description'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        df = handler.load_file()
        
        assert len(df) == 3
        assert 'job_id' in df.columns
        assert 'description' in df.columns
    
    def test_load_excel(self, sample_excel, mock_config_dict):
        """Test loading Excel file."""
        mock_config_dict['input']['file_path'] = sample_excel
        mock_config_dict['input']['columns']['text_column'] = 'description'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        df = handler.load_file()
        
        assert len(df) == 3
        assert 'description' in df.columns
    
    def test_file_not_found(self, mock_config_dict):
        """Test error when file doesn't exist."""
        mock_config_dict['input']['file_path'] = 'nonexistent.csv'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        
        with pytest.raises(InputError) as exc_info:
            handler.load_file()
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_missing_text_column(self, sample_csv, mock_config_dict):
        """Test error when text column is missing."""
        mock_config_dict['input']['file_path'] = sample_csv
        mock_config_dict['input']['columns']['text_column'] = 'nonexistent_column'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        
        with pytest.raises(InputError) as exc_info:
            handler.load_file()
        
        assert "nonexistent_column" in str(exc_info.value)
        assert "description" in str(exc_info.value)  # Should list available columns
    
    def test_auto_generate_ids(self, sample_csv, mock_config_dict):
        """Test automatic ID generation."""
        mock_config_dict['input']['file_path'] = sample_csv
        mock_config_dict['input']['columns']['text_column'] = 'description'
        mock_config_dict['input']['columns']['id_column'] = None
        mock_config_dict['input']['id_prefix'] = 'test'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        df = handler.load_file()
        
        assert 'job_id' in df.columns
        assert df['job_id'].iloc[0].startswith('test_')
        assert len(df['job_id'].unique()) == len(df)
    
    def test_use_existing_ids(self, sample_csv, mock_config_dict):
        """Test using existing ID column."""
        mock_config_dict['input']['file_path'] = sample_csv
        mock_config_dict['input']['columns']['text_column'] = 'description'
        mock_config_dict['input']['columns']['id_column'] = 'job_id'
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        df = handler.load_file()
        
        assert 'job_id' in df.columns
        assert df['job_id'].iloc[0] == 'jd_001'
    
    def test_detect_file_type(self, mock_config_dict):
        """Test file type detection."""
        config = MockConfig(mock_config_dict)
        handler = InputHandler(config)
        
        assert handler._detect_file_type("test.csv") == "csv"
        assert handler._detect_file_type("test.xlsx") == "xlsx"
        assert handler._detect_file_type("test.xls") == "xlsx"
    
    def test_unsupported_format(self, mock_config_dict):
        """Test error for unsupported file format."""
        config = MockConfig(mock_config_dict)
        handler = InputHandler(config)
        
        with pytest.raises(InputError) as exc_info:
            handler._detect_file_type("test.txt")
        
        assert "unsupported" in str(exc_info.value).lower()


class TestInputHandlerChunked:
    """Test chunked loading for large files."""
    
    def test_chunked_csv_loading(self, tmp_path, mock_config_dict):
        """Test loading CSV in chunks."""
        # Create test CSV with 100 rows
        csv_path = tmp_path / "large.csv"
        df = pd.DataFrame({
            'id': range(100),
            'description': [f'Description {i}' for i in range(100)]
        })
        df.to_csv(csv_path, index=False)
        
        mock_config_dict['input']['file_path'] = str(csv_path)
        mock_config_dict['input']['columns']['text_column'] = 'description'
        mock_config_dict['input']['chunk_size'] = 30
        config = MockConfig(mock_config_dict)
        
        handler = InputHandler(config)
        chunks = list(handler.load_file_chunked())
        
        assert len(chunks) == 4  # 100 / 30 = 4 (with remainder)
        assert len(chunks[0]) == 30
        assert len(chunks[-1]) == 10  # Remainder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
