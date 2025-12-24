"""
Rules Generator for JSONL Export

Tasks: T8.1 - T8.6

This module provides:
- JSONL format rule export
- Skill variations inclusion
- Metadata (category, pattern_type, is_core_skill)
- Min frequency filtering

Usage:
    from src.features import RulesGenerator
    
    generator = RulesGenerator(config, dictionary)
    generator.generate_all(df)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from src.features.skill_dictionary import SkillDictionary
from src.features.aggregator import Aggregator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RulesGenerator:
    """
    Generate extraction rules in JSONL format.
    
    Rules include skill patterns with metadata:
    - Variations for each skill
    - Category (technical/soft/custom)
    - Frequency statistics
    - Core skill flag (>50% threshold)
    
    Usage:
        generator = RulesGenerator(config, dictionary)
        output_paths = generator.generate_all(df)
    """
    
    def __init__(self, config, skill_dictionary: SkillDictionary):
        """
        Initialize rules generator.
        
        Args:
            config: ConfigLoader instance
            skill_dictionary: Loaded SkillDictionary instance
        """
        self.config = config
        self.dictionary = skill_dictionary
        self.aggregator = Aggregator(config)
        
        self.output_dir = Path(config.get("rules.output_dir", "reports/rules"))
        self.min_frequency = config.get("rules.min_frequency_threshold", 2)
        self.core_threshold = config.get("rules.core_skill_threshold", 0.5)
        
        # Load variations for rule enrichment
        self.variations: Dict[str, List[str]] = {}
        self._load_variations()
        
        # Ensure directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "role_rules").mkdir(exist_ok=True)
    
    def _load_variations(self) -> None:
        """Load skill variations for rule enrichment."""
        variations_file = self.config.get("extraction.variations_file")
        
        if not variations_file:
            return
        
        path = Path(variations_file)
        if not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.variations = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load variations: {e}")
    
    def generate_all(self, df) -> Dict[str, str]:
        """
        Generate all rule files.
        
        Args:
            df: DataFrame with extraction results
            
        Returns:
            Dict mapping output type to file path(s)
        """
        output_paths = {}
        
        # Global rules
        output_paths['global'] = self.generate_global_rules(df)
        
        # Role-specific rules
        output_paths['roles'] = self.generate_role_rules(df)
        
        return output_paths
    
    def generate_global_rules(self, df) -> str:
        """
        Generate global rules JSONL file.
        
        Args:
            df: Full DataFrame
            
        Returns:
            Path to output file
        """
        aggregation = self.aggregator._aggregate_group(df)
        total_jds = aggregation['total_jds']
        
        output_path = self.output_dir / "global_rules.jsonl"
        
        rules_written = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for skill, count in aggregation['skill_frequencies'].items():
                # Apply minimum frequency filter
                if count < self.min_frequency:
                    continue
                
                rule = self._create_rule(
                    skill=skill,
                    count=count,
                    total_jds=total_jds,
                    rank=self._get_rank(skill, aggregation['top_skills'])
                )
                
                f.write(json.dumps(rule, ensure_ascii=False) + '\n')
                rules_written += 1
        
        logger.info(f"Generated {rules_written} global rules: {output_path}")
        return str(output_path)
    
    def generate_role_rules(self, df) -> Dict[str, str]:
        """
        Generate per-role rule files.
        
        Args:
            df: DataFrame with extraction results
            
        Returns:
            Dict mapping role -> file path
        """
        role_aggregations = self.aggregator.aggregate_by_role(df)
        output_paths = {}
        
        for role, data in role_aggregations.items():
            # Sanitize role name for filename
            safe_role = "".join(c if c.isalnum() else "_" for c in str(role))
            output_path = self.output_dir / "role_rules" / f"{safe_role}_rules.jsonl"
            
            total_jds = data['total_jds']
            
            rules_written = 0
            with open(output_path, 'w', encoding='utf-8') as f:
                for skill, count in data['skill_frequencies'].items():
                    if count < self.min_frequency:
                        continue
                    
                    rule = self._create_rule(
                        skill=skill,
                        count=count,
                        total_jds=total_jds,
                        rank=self._get_rank(skill, data['top_skills']),
                        role=role
                    )
                    
                    f.write(json.dumps(rule, ensure_ascii=False) + '\n')
                    rules_written += 1
            
            output_paths[role] = str(output_path)
            logger.debug(f"Generated {rules_written} rules for role: {role}")
        
        logger.info(f"Generated rules for {len(role_aggregations)} roles")
        return output_paths
    
    def _create_rule(
        self,
        skill: str,
        count: int,
        total_jds: int,
        rank: Optional[int] = None,
        role: Optional[str] = None
    ) -> Dict:
        """
        Create a single rule entry.
        
        Args:
            skill: Skill name
            count: Document frequency
            total_jds: Total JDs in group
            rank: Rank in top-N (None if not in top)
            role: Role name (None for global)
            
        Returns:
            Rule dictionary
        """
        percentage = (count / total_jds) * 100 if total_jds > 0 else 0
        is_core = percentage >= (self.core_threshold * 100)
        
        rule = {
            'skill': skill,
            'pattern': skill,  # Base pattern (skill name itself)
            'variations': self._get_variations(skill),
            'category': self.dictionary.get_category(skill) or 'unknown',
            'pattern_type': 'dictionary',
            'frequency': count,
            'percentage': round(percentage, 2),
            'is_core_skill': is_core
        }
        
        if rank is not None:
            rule['rank'] = rank
        
        if role is not None:
            rule['role'] = role
        
        return rule
    
    def _get_variations(self, skill: str) -> List[str]:
        """Get all variations for a skill."""
        skill_lower = skill.lower()
        
        # Check if this skill is a canonical form
        for canonical, variations in self.variations.items():
            if canonical.lower() == skill_lower:
                return variations
            # Check if skill is a variation
            if skill_lower in [v.lower() for v in variations]:
                return [canonical] + variations
        
        return [skill]  # Just the skill itself
    
    def _get_rank(self, skill: str, top_skills: List[Dict]) -> Optional[int]:
        """Get rank of skill in top-N list."""
        for i, entry in enumerate(top_skills, 1):
            if entry['skill'] == skill:
                return i
        return None


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("RulesGenerator module loaded successfully!")
    print("Use RulesGenerator(config, dictionary).generate_all(df) to generate rules.")
