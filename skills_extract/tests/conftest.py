"""
Pytest Configuration and Shared Fixtures

This file provides reusable fixtures for all tests.
Fixtures are automatically discovered by pytest.
"""

import pytest
import yaml
import pandas as pd
from pathlib import Path


# =============================================================================
# Directory Fixtures
# =============================================================================

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    return data_dir


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with job descriptions."""
    return pd.DataFrame({
        'job_id': ['jd_001', 'jd_002', 'jd_003'],
        'job_title': ['Data Engineer', 'Software Developer', 'Data Scientist'],
        'description': [
            'Looking for Python developer with AWS and SQL experience. Must know Docker.',
            'Java and Spring Boot required. Experience with React preferred.',
            'Data scientist with machine learning and Python. TensorFlow a plus.'
        ]
    })


@pytest.fixture
def sample_csv(tmp_path, sample_dataframe):
    """Create a sample CSV file and return its path."""
    csv_path = tmp_path / "data" / "raw" / "test_jobs.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    sample_dataframe.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_excel(tmp_path, sample_dataframe):
    """Create a sample Excel file and return its path."""
    excel_path = tmp_path / "data" / "raw" / "test_jobs.xlsx"
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    sample_dataframe.to_excel(excel_path, index=False)
    return str(excel_path)


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def mock_config_dict(tmp_path):
    """Create a mock configuration dictionary."""
    return {
        'pipeline': {
            'name': 'test_pipeline',
            'version': '1.0.0'
        },
        'input': {
            'file_path': str(tmp_path / 'data' / 'raw' / 'test.csv'),
            'file_type': 'auto',
            'encoding': 'auto',
            'columns': {
                'text_column': 'description',
                'id_column': 'job_id',
                'title_column': 'job_title',
                'role_column': None
            },
            'id_prefix': 'jd',
            'chunk_size': 1000
        },
        'preprocessing': {
            'lowercase': True,
            'normalize_whitespace': True,
            'remove_special_chars': True,
            'preserve_hyphens': True,
            'expand_abbreviations': False
        },
        'extraction': {
            'dictionaries': {
                'technical': str(tmp_path / 'references' / 'dictionaries' / 'technical.txt'),
                'soft': str(tmp_path / 'references' / 'dictionaries' / 'soft.txt'),
                'custom': None
            },
            'normalize_skills': True,
            'variations_file': str(tmp_path / 'references' / 'dictionaries' / 'variations.yaml'),
            'case_sensitive': False,
            'remove_duplicates': True
        },
        'output': {
            'directory': str(tmp_path / 'data' / 'processed'),
            'formats': ['csv', 'json'],
            'csv': {
                'filename': 'extracted_skills.csv',
                'skills_format': 'comma_separated',
                'include_columns': ['job_id', 'extracted_skills', 'skill_count']
            },
            'json': {
                'filename': 'extracted_skills.json',
                'indent': 2
            }
        },
        'logging': {
            'level': 'DEBUG',
            'file': str(tmp_path / 'reports' / 'test.log'),
            'console': False,
            'format': '%(levelname)s - %(message)s'
        },
        'analytics': {
            'enabled': False,
            'top_n_skills': 20,
            'output_dir': str(tmp_path / 'reports' / 'analytics')
        },
        'rules': {
            'enabled': False,
            'min_frequency_threshold': 2,
            'core_skill_threshold': 0.5,
            'output_dir': str(tmp_path / 'reports' / 'rules')
        }
    }


@pytest.fixture
def sample_config_yaml(tmp_path, mock_config_dict):
    """Create a sample config.yaml file and return its path."""
    config_dir = tmp_path / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    
    with open(config_path, 'w') as f:
        yaml.dump(mock_config_dict, f)
    
    return str(config_path)


# =============================================================================
# Dictionary Fixtures
# =============================================================================

@pytest.fixture
def sample_skills_file(tmp_path):
    """Create a sample skills dictionary file."""
    dict_dir = tmp_path / "references" / "dictionaries"
    dict_dir.mkdir(parents=True, exist_ok=True)
    skills_file = dict_dir / "technical.txt"
    
    skills = """# Technical Skills
Python
Java
JavaScript
SQL
AWS
Docker
Kubernetes
React
Spring Boot
TensorFlow
Machine Learning
"""
    skills_file.write_text(skills)
    return str(skills_file)


@pytest.fixture
def sample_soft_skills_file(tmp_path):
    """Create a sample soft skills file."""
    dict_dir = tmp_path / "references" / "dictionaries"
    dict_dir.mkdir(parents=True, exist_ok=True)
    skills_file = dict_dir / "soft.txt"
    
    skills = """# Soft Skills
Communication
Leadership
Teamwork
Problem Solving
"""
    skills_file.write_text(skills)
    return str(skills_file)


@pytest.fixture
def sample_variations_file(tmp_path):
    """Create a sample skill variations file."""
    dict_dir = tmp_path / "references" / "dictionaries"
    dict_dir.mkdir(parents=True, exist_ok=True)
    variations_file = dict_dir / "variations.yaml"
    
    variations = {
        'JavaScript': ['JS', 'Javascript', 'java script'],
        'Python': ['python3', 'py'],
        'Machine Learning': ['ML', 'machine-learning'],
        'Amazon Web Services': ['AWS', 'amazon web services'],
        'Kubernetes': ['K8s', 'k8']
    }
    
    with open(variations_file, 'w') as f:
        yaml.dump(variations, f)
    
    return str(variations_file)


# =============================================================================
# Mock Config Class
# =============================================================================

class MockConfig:
    """
    Mock ConfigLoader for testing.
    
    Usage in tests:
        config = MockConfig(mock_config_dict)
        handler = InputHandler(config)
    """
    
    def __init__(self, config_dict):
        self._config = config_dict
    
    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_input_config(self):
        return self._config.get('input', {})
    
    def get_extraction_config(self):
        return self._config.get('extraction', {})
    
    def get_output_config(self):
        return self._config.get('output', {})


@pytest.fixture
def mock_config(mock_config_dict):
    """Create a MockConfig instance."""
    return MockConfig(mock_config_dict)
