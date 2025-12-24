"""
Aggregator for Analytics

Tasks: T7.2 - T7.6

This module provides:
- Document frequency calculation (not word count)
- Role-level aggregation
- Top-N rankings
- Percentage calculations

Usage:
    from src.features import Aggregator
    
    aggregator = Aggregator(config)
    role_stats = aggregator.aggregate_by_role(df)
"""

from typing import Dict, List, Optional
from collections import Counter
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Aggregator:
    """
    Aggregate extraction results for analytics.
    
    Calculates document frequencies (number of JDs containing each skill)
    rather than word counts, providing more meaningful metrics.
    
    Usage:
        aggregator = Aggregator(config)
        role_stats = aggregator.aggregate_by_role(df)
    """
    
    def __init__(self, config):
        """
        Initialize aggregator.
        
        Args:
            config: ConfigLoader instance
        """
        self.config = config
        self.role_column = config.get("input.columns.role_column")
        self.top_n = config.get("analytics.top_n_skills", 20)
        
        # Role normalization mappings
        self.role_mappings = config.get("analytics.role_mappings", {})
    
    def normalize_role(self, role) -> str:
        """
        Normalize role name using configured mappings.
        
        Args:
            role: Raw role name
            
        Returns:
            Normalized role name
        """
        if not role or pd.isna(role):
            return "Unknown"
        
        role_lower = str(role).lower().strip()
        
        # Check mappings
        for canonical, variations in self.role_mappings.items():
            if role_lower in [v.lower() for v in variations]:
                return canonical
        
        return str(role).strip()
    
    def calculate_document_frequency(
        self, 
        df: pd.DataFrame
    ) -> Dict[str, int]:
        """
        Calculate document frequency for each skill.
        
        Document frequency = number of JDs containing the skill
        (NOT total occurrences across all JDs)
        
        Args:
            df: DataFrame with 'extracted_skills' column
            
        Returns:
            Dict mapping skill -> document count
        """
        skill_counts = Counter()
        
        for skills in df['extracted_skills']:
            # Count each skill once per document
            unique_skills = set(skills) if isinstance(skills, list) else set()
            skill_counts.update(unique_skills)
        
        return dict(skill_counts)
    
    def aggregate_by_role(
        self, 
        df: pd.DataFrame
    ) -> Dict[str, Dict]:
        """
        Aggregate skills by role.
        
        Args:
            df: DataFrame with extracted skills and role column
            
        Returns:
            Dict mapping role -> aggregation results
        """
        if not self.role_column or self.role_column not in df.columns:
            logger.warning("Role column not found, aggregating as single group")
            return {"all": self._aggregate_group(df)}
        
        # Normalize roles
        df = df.copy()
        df['normalized_role'] = df[self.role_column].apply(self.normalize_role)
        
        results = {}
        
        for role, group in df.groupby('normalized_role'):
            results[role] = self._aggregate_group(group)
            logger.debug(f"Aggregated {len(group)} JDs for role: {role}")
        
        return results
    
    def _aggregate_group(self, df: pd.DataFrame) -> Dict:
        """
        Aggregate a single group (role or entire dataset).
        
        Args:
            df: DataFrame subset
            
        Returns:
            Aggregation results
        """
        total_jds = len(df)
        skill_frequencies = self.calculate_document_frequency(df)
        
        # Calculate percentages
        skill_percentages = {
            skill: (count / total_jds) * 100 if total_jds > 0 else 0
            for skill, count in skill_frequencies.items()
        }
        
        # Get top-N skills
        top_skills = sorted(
            skill_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.top_n]
        
        # Calculate average skills per JD
        avg_skills = df['skill_count'].mean() if 'skill_count' in df.columns and len(df) > 0 else 0
        
        return {
            'total_jds': total_jds,
            'unique_skills': len(skill_frequencies),
            'skill_frequencies': skill_frequencies,
            'skill_percentages': skill_percentages,
            'top_skills': [
                {
                    'skill': skill,
                    'count': count,
                    'percentage': round(skill_percentages[skill], 2)
                }
                for skill, count in top_skills
            ],
            'avg_skills_per_jd': round(avg_skills, 2)
        }
    
    def get_dataset_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate dataset-level summary statistics.
        
        Args:
            df: Full DataFrame
            
        Returns:
            Summary statistics dict
        """
        skill_frequencies = self.calculate_document_frequency(df)
        
        skill_counts = df['skill_count'] if 'skill_count' in df.columns else pd.Series([0])
        
        return {
            'total_jds_processed': len(df),
            'unique_skills_extracted': len(skill_frequencies),
            'total_skill_extractions': int(skill_counts.sum()),
            'avg_skills_per_jd': round(skill_counts.mean(), 2) if len(df) > 0 else 0,
            'median_skills_per_jd': round(skill_counts.median(), 2) if len(df) > 0 else 0,
            'max_skills_in_single_jd': int(skill_counts.max()) if len(df) > 0 else 0,
            'min_skills_in_single_jd': int(skill_counts.min()) if len(df) > 0 else 0
        }


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("Aggregator module loaded successfully!")
    print("Use Aggregator(config).aggregate_by_role(df) to aggregate results.")
