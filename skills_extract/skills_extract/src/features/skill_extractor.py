"""
Skill Extractor

Tasks: T4.4 - T4.6

This module provides:
- Dictionary-based skill extraction
- Pattern matching with word boundaries
- Skill normalization (variations → canonical names)
- Duplicate removal per document

Usage:
    from src.features import SkillExtractor, SkillDictionary
    
    dictionary = SkillDictionary(config)
    dictionary.load_all()
    
    extractor = SkillExtractor(config, dictionary)
    skills = extractor.extract(text)
"""

import re
import yaml
from pathlib import Path
from typing import List, Set, Dict, Optional
import pandas as pd
from src.features.skill_dictionary import SkillDictionary
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SkillExtractor:
    """
    Extract skills from job description text.
    
    Uses dictionary-based matching with support for
    skill normalization and variation handling.
    
    Usage:
        extractor = SkillExtractor(config, dictionary)
        skills = extractor.extract(text)
        
        # Batch extraction
        df = extractor.extract_batch(df, text_column='processed_text')
    """
    
    def __init__(self, config, skill_dictionary: SkillDictionary):
        """
        Initialize extractor.
        
        Args:
            config: ConfigLoader instance
            skill_dictionary: Loaded SkillDictionary instance
        """
        self.config = config
        self.dictionary = skill_dictionary
        
        # Settings
        self.case_sensitive = config.get("extraction.case_sensitive", False)
        self.remove_duplicates = config.get("extraction.remove_duplicates", True)
        self.normalize_skills = config.get("extraction.normalize_skills", True)
        
        # Load skill variations for normalization
        self.variations: Dict[str, List[str]] = {}
        self._variation_map: Dict[str, str] = {}  # variation -> canonical
        if self.normalize_skills:
            self._load_variations()
        
        # Build regex patterns for efficient matching
        self._build_patterns()
        
        # Statistics
        self._stats = {
            'total_extractions': 0,
            'total_skills_found': 0,
            'unique_skills_found': set()
        }
    
    def _build_patterns(self) -> None:
        """
        Build regex patterns from skill dictionary.
        
        Creates patterns for both single-word and multi-word skills.
        """
        all_skills = self.dictionary.get_all_skills()
        
        # Also include variations as matchable patterns
        all_patterns = set(all_skills)
        for variations in self.variations.values():
            all_patterns.update(v.lower() for v in variations)
        
        # Sort by length (longest first) to match multi-word skills before parts
        sorted_skills = sorted(all_patterns, key=len, reverse=True)
        
        if not sorted_skills:
            logger.warning("No skills in dictionary. Extraction will return empty results.")
            self._pattern = None
            return
        
        # Escape special regex characters
        escaped_skills = [re.escape(skill) for skill in sorted_skills]
        
        # Build pattern with word boundaries
        pattern_str = r'\b(' + '|'.join(escaped_skills) + r')\b'
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._pattern = re.compile(pattern_str, flags)
        
        logger.debug(f"Built pattern for {len(sorted_skills)} skills/variations")
    
    def _load_variations(self) -> None:
        """Load skill variations for normalization."""
        variations_file = self.config.get("extraction.variations_file")
        
        if not variations_file:
            return
        
        path = Path(variations_file)
        if not path.exists():
            logger.warning(f"Variations file not found: {variations_file}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.variations = yaml.safe_load(f) or {}
            
            # Build reverse mapping: variation -> canonical
            for canonical, variations in self.variations.items():
                canonical_lower = canonical.lower()
                for variation in variations:
                    self._variation_map[variation.lower()] = canonical_lower
            
            logger.info(f"Loaded variations for {len(self.variations)} skills")
        except Exception as e:
            logger.error(f"Failed to load variations: {e}")
    
    def extract(self, text: str) -> List[str]:
        """
        Extract skills from a single text.
        
        Args:
            text: Preprocessed text to extract from
            
        Returns:
            List of extracted skills
        """
        if not text or not isinstance(text, str):
            return []
        
        if self._pattern is None:
            return []
        
        # Find all matches
        matches = self._pattern.findall(text)
        
        # Normalize case for consistency
        skills = [match.lower() for match in matches]
        
        # Apply skill normalization (variations → canonical)
        if self.normalize_skills:
            skills = [self._normalize_skill(skill) for skill in skills]
        
        # Remove duplicates (preserve order)
        if self.remove_duplicates:
            skills = self._remove_duplicates_preserve_order(skills)
        
        # Update stats
        self._stats['total_extractions'] += 1
        self._stats['total_skills_found'] += len(skills)
        self._stats['unique_skills_found'].update(skills)
        
        return skills
    
    def _normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name using variations mapping.
        
        Args:
            skill: Skill name to normalize
            
        Returns:
            Canonical skill name
        """
        skill_lower = skill.lower()
        
        # Check if this is a variation
        if skill_lower in self._variation_map:
            return self._variation_map[skill_lower]
        
        return skill_lower
    
    def _remove_duplicates_preserve_order(self, skills: List[str]) -> List[str]:
        """
        Remove duplicates while preserving first occurrence order.
        
        Args:
            skills: List with potential duplicates
            
        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        
        for skill in skills:
            if skill not in seen:
                seen.add(skill)
                result.append(skill)
        
        return result
    
    def extract_batch(
        self, 
        df: pd.DataFrame, 
        text_column: str = 'processed_text'
    ) -> pd.DataFrame:
        """
        Extract skills from DataFrame batch.
        
        Args:
            df: DataFrame with text column
            text_column: Column containing text to extract from
            
        Returns:
            DataFrame with 'extracted_skills' and 'skill_count' columns
        """
        df = df.copy()
        
        logger.info(f"Extracting skills from {len(df)} records")
        
        # Extract skills for each row
        df['extracted_skills'] = df[text_column].apply(self.extract)
        
        # Add skill count
        df['skill_count'] = df['extracted_skills'].apply(len)
        
        # Log summary
        total_skills = df['skill_count'].sum()
        avg_skills = df['skill_count'].mean() if len(df) > 0 else 0
        
        logger.info(
            f"Extraction complete: {total_skills} total skills, "
            f"{avg_skills:.1f} avg per JD"
        )
        
        return df
    
    def get_extraction_stats(self) -> Dict:
        """Get extraction statistics."""
        return {
            'total_extractions': self._stats['total_extractions'],
            'total_skills_found': self._stats['total_skills_found'],
            'unique_skills_count': len(self._stats['unique_skills_found']),
            'unique_skills': sorted(list(self._stats['unique_skills_found']))
        }
    
    def reset_stats(self) -> None:
        """Reset extraction statistics."""
        self._stats = {
            'total_extractions': 0,
            'total_skills_found': 0,
            'unique_skills_found': set()
        }


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("SkillExtractor module loaded successfully!")
    print("Use SkillExtractor(config, dictionary).extract(text) to extract skills.")
