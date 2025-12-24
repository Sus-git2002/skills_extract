"""
Skill Dictionary Manager

Tasks: T4.1, T4.7

This module provides:
- Loading skills from text files
- Multiple dictionary support (technical, soft, custom)
- Skill categorization
- Deduplication

Usage:
    from src.features import SkillDictionary
    
    dictionary = SkillDictionary(config)
    dictionary.load_all()
    skills = dictionary.get_all_skills()
"""

from pathlib import Path
from typing import Set, Dict, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SkillDictionary:
    """
    Manage skill dictionaries for extraction.
    
    Supports loading skills from multiple files and
    organizing them by category (technical, soft, custom).
    
    Usage:
        dictionary = SkillDictionary(config)
        dictionary.load_all()
        skills = dictionary.get_all_skills()
    """
    
    def __init__(self, config):
        """
        Initialize skill dictionary manager.
        
        Args:
            config: ConfigLoader instance
        """
        self.config = config
        
        # Skill storage by category
        self._skills: Dict[str, Set[str]] = {
            'technical': set(),
            'soft': set(),
            'custom': set()
        }
        
        # Combined set for quick lookup
        self._all_skills: Set[str] = set()
        
        # Track loading stats
        self._stats = {
            'total_loaded': 0,
            'duplicates_removed': 0,
            'files_loaded': 0
        }
    
    def load_all(self) -> None:
        """Load all configured skill dictionaries."""
        dict_config = self.config.get("extraction.dictionaries", {})
        
        # Load technical skills
        if dict_config.get("technical"):
            self._skills['technical'] = self.load_from_file(
                dict_config["technical"], 
                category="technical"
            )
        
        # Load soft skills
        if dict_config.get("soft"):
            self._skills['soft'] = self.load_from_file(
                dict_config["soft"],
                category="soft"
            )
        
        # Load custom skills (optional)
        if dict_config.get("custom"):
            self._skills['custom'] = self.load_from_file(
                dict_config["custom"],
                category="custom"
            )
        
        # Build combined set
        self._all_skills = set()
        for category_skills in self._skills.values():
            self._all_skills.update(category_skills)
        
        self._stats['total_loaded'] = len(self._all_skills)
        
        logger.info(
            f"Loaded {self._stats['total_loaded']} unique skills: "
            f"{len(self._skills['technical'])} technical, "
            f"{len(self._skills['soft'])} soft, "
            f"{len(self._skills['custom'])} custom"
        )
    
    def load_from_file(self, file_path: str, category: str = "custom") -> Set[str]:
        """
        Load skills from a text file.
        
        File format: One skill per line, # for comments
        
        Args:
            file_path: Path to skill file
            category: Category label for logging
            
        Returns:
            Set of normalized skill names
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Skill file not found: {file_path}")
            return set()
        
        skills = set()
        duplicates = 0
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Strip whitespace
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Normalize skill name (lowercase for matching)
                skill = line.lower()
                
                if skill in skills:
                    logger.debug(f"Duplicate skill at line {line_num}: {line}")
                    duplicates += 1
                else:
                    skills.add(skill)
        
        self._stats['duplicates_removed'] += duplicates
        self._stats['files_loaded'] += 1
        
        logger.debug(f"Loaded {len(skills)} skills from {file_path}")
        return skills
    
    def get_all_skills(self) -> Set[str]:
        """Get all skills across all categories."""
        return self._all_skills.copy()
    
    def get_skills_by_category(self, category: str) -> Set[str]:
        """
        Get skills for a specific category.
        
        Args:
            category: 'technical', 'soft', or 'custom'
            
        Returns:
            Set of skills in that category
        """
        return self._skills.get(category, set()).copy()
    
    def add_skill(self, skill: str, category: str = "custom") -> None:
        """
        Add a skill programmatically.
        
        Args:
            skill: Skill name to add
            category: Category to add to
        """
        normalized = skill.lower()
        self._skills[category].add(normalized)
        self._all_skills.add(normalized)
    
    def contains(self, skill: str) -> bool:
        """Check if skill exists in any dictionary."""
        return skill.lower() in self._all_skills
    
    def get_category(self, skill: str) -> Optional[str]:
        """
        Get the category of a skill.
        
        Args:
            skill: Skill name to look up
            
        Returns:
            Category name or None if not found
        """
        normalized = skill.lower()
        for category, skills in self._skills.items():
            if normalized in skills:
                return category
        return None
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get loading statistics."""
        return self._stats.copy()
    
    def __len__(self) -> int:
        """Return total number of unique skills."""
        return len(self._all_skills)
    
    def __contains__(self, skill: str) -> bool:
        """Allow 'skill in dictionary' syntax."""
        return self.contains(skill)


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("SkillDictionary module loaded successfully!")
    print("Use SkillDictionary(config).load_all() to load dictionaries.")
