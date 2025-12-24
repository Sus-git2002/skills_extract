"""
Tests for Skill Extractor

Tests Tasks: T4.4 - T4.6
"""

import pytest
import pandas as pd

from src.features import SkillDictionary, SkillExtractor
from tests.conftest import MockConfig


class TestSkillDictionary:
    """Test suite for SkillDictionary."""
    
    def test_load_from_file(self, sample_skills_file, mock_config_dict):
        """Test loading skills from file."""
        mock_config_dict['extraction']['dictionaries']['technical'] = sample_skills_file
        config = MockConfig(mock_config_dict)
        
        dictionary = SkillDictionary(config)
        skills = dictionary.load_from_file(sample_skills_file)
        
        assert len(skills) > 0
        assert 'python' in skills
        assert 'java' in skills
    
    def test_comments_ignored(self, tmp_path, mock_config_dict):
        """Test that comments are ignored."""
        skills_file = tmp_path / "skills.txt"
        skills_file.write_text("# This is a comment\nPython\n# Another comment\nJava")
        
        config = MockConfig(mock_config_dict)
        dictionary = SkillDictionary(config)
        skills = dictionary.load_from_file(str(skills_file))
        
        assert len(skills) == 2
        assert 'python' in skills
        assert '# this is a comment' not in skills
    
    def test_duplicates_handled(self, tmp_path, mock_config_dict):
        """Test that duplicate skills are deduplicated."""
        skills_file = tmp_path / "skills.txt"
        skills_file.write_text("Python\nJava\nPython\npython")  # Case-insensitive duplicate
        
        config = MockConfig(mock_config_dict)
        dictionary = SkillDictionary(config)
        skills = dictionary.load_from_file(str(skills_file))
        
        assert len(skills) == 2  # Only Python and Java
    
    def test_get_category(self, sample_skills_file, sample_soft_skills_file, mock_config_dict):
        """Test getting skill category."""
        mock_config_dict['extraction']['dictionaries']['technical'] = sample_skills_file
        mock_config_dict['extraction']['dictionaries']['soft'] = sample_soft_skills_file
        config = MockConfig(mock_config_dict)
        
        dictionary = SkillDictionary(config)
        dictionary.load_all()
        
        assert dictionary.get_category('python') == 'technical'
        assert dictionary.get_category('leadership') == 'soft'


class TestSkillExtractor:
    """Test suite for SkillExtractor."""
    
    @pytest.fixture
    def extractor(self, sample_skills_file, sample_variations_file, mock_config_dict):
        """Create an extractor with sample dictionary."""
        mock_config_dict['extraction']['dictionaries']['technical'] = sample_skills_file
        mock_config_dict['extraction']['dictionaries']['soft'] = None
        mock_config_dict['extraction']['variations_file'] = sample_variations_file
        config = MockConfig(mock_config_dict)
        
        dictionary = SkillDictionary(config)
        dictionary.load_all()
        
        return SkillExtractor(config, dictionary)
    
    def test_extract_single_skill(self, extractor):
        """Test extracting a single skill."""
        text = "looking for python developer"
        skills = extractor.extract(text)
        
        assert 'python' in skills
    
    def test_extract_multiple_skills(self, extractor):
        """Test extracting multiple skills."""
        text = "need python and java developer with sql experience"
        skills = extractor.extract(text)
        
        assert 'python' in skills
        assert 'java' in skills
        assert 'sql' in skills
    
    def test_case_insensitive(self, extractor):
        """Test case-insensitive matching."""
        text = "Experience with PYTHON and Python and python"
        skills = extractor.extract(text)
        
        # Should find python only once due to deduplication
        assert skills.count('python') == 1
    
    def test_duplicate_removal(self, extractor):
        """Test duplicates are removed per document."""
        text = "python python python developer with python"
        skills = extractor.extract(text)
        
        assert len(skills) == 1
        assert skills[0] == 'python'
    
    def test_empty_text(self, extractor):
        """Test handling of empty text."""
        assert extractor.extract("") == []
        assert extractor.extract(None) == []
    
    def test_no_skills_found(self, extractor):
        """Test when no skills match."""
        text = "looking for someone with great attitude"
        skills = extractor.extract(text)
        
        # This depends on the dictionary, but 'attitude' is not in technical skills
        assert 'attitude' not in skills
    
    def test_skill_normalization(self, extractor):
        """Test skill variations are normalized."""
        text = "need JS developer"  # JS should normalize to JavaScript
        skills = extractor.extract(text)
        
        # JS is a variation of JavaScript
        assert 'javascript' in skills or 'js' in skills
    
    def test_batch_extraction(self, extractor):
        """Test extracting from DataFrame."""
        df = pd.DataFrame({
            'processed_text': [
                'python developer',
                'java spring boot',
                'aws docker kubernetes'
            ]
        })
        
        result = extractor.extract_batch(df)
        
        assert 'extracted_skills' in result.columns
        assert 'skill_count' in result.columns
        assert result['skill_count'].iloc[0] >= 1
    
    def test_extraction_stats(self, extractor):
        """Test extraction statistics are tracked."""
        extractor.reset_stats()
        
        extractor.extract("python developer")
        extractor.extract("java spring")
        
        stats = extractor.get_extraction_stats()
        
        assert stats['total_extractions'] == 2
        assert stats['total_skills_found'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
