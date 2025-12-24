"""
Analytics Generator

Tasks: T7.7

This module provides:
- Dataset-level analytics JSON
- Role-level analytics JSON
- Formatted statistics output

Usage:
    from src.visualization import AnalyticsGenerator
    
    generator = AnalyticsGenerator(config)
    generator.generate_all(df)
"""

import json
from pathlib import Path
from typing import Dict
from src.features.aggregator import Aggregator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsGenerator:
    """
    Generate analytics JSON files.
    
    Creates both dataset-level and role-level analytics files.
    
    Usage:
        generator = AnalyticsGenerator(config)
        output_paths = generator.generate_all(df)
    """
    
    def __init__(self, config):
        """
        Initialize analytics generator.
        
        Args:
            config: ConfigLoader instance
        """
        self.config = config
        self.aggregator = Aggregator(config)
        self.output_dir = Path(config.get("analytics.output_dir", "reports/analytics"))
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "role_analytics").mkdir(exist_ok=True)
    
    def generate_all(self, df) -> Dict[str, str]:
        """
        Generate all analytics files.
        
        Args:
            df: DataFrame with extraction results
            
        Returns:
            Dict mapping output type to file path
        """
        output_paths = {}
        
        # Dataset-level analytics
        output_paths['dataset'] = self.generate_dataset_analytics(df)
        
        # Role-level analytics
        output_paths['roles'] = self.generate_role_analytics(df)
        
        return output_paths
    
    def generate_dataset_analytics(self, df) -> str:
        """
        Generate dataset-level analytics JSON.
        
        Args:
            df: Full DataFrame
            
        Returns:
            Path to output file
        """
        summary = self.aggregator.get_dataset_summary(df)
        full_aggregation = self.aggregator._aggregate_group(df)
        
        analytics = {
            'summary': summary,
            'skill_rankings': full_aggregation['top_skills'],
            'all_skill_frequencies': full_aggregation['skill_frequencies'],
            'all_skill_percentages': full_aggregation['skill_percentages']
        }
        
        output_path = self.output_dir / "dataset_analytics.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated dataset analytics: {output_path}")
        return str(output_path)
    
    def generate_role_analytics(self, df) -> Dict[str, str]:
        """
        Generate per-role analytics JSON files.
        
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
            output_path = self.output_dir / "role_analytics" / f"{safe_role}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            output_paths[role] = str(output_path)
            logger.debug(f"Generated analytics for role: {role}")
        
        logger.info(f"Generated analytics for {len(role_aggregations)} roles")
        return output_paths


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("AnalyticsGenerator module loaded successfully!")
    print("Use AnalyticsGenerator(config).generate_all(df) to generate analytics.")
