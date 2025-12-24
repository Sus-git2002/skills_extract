"""
Output Handler for Extraction Results

Tasks: T5.1 - T5.4

This module provides:
- CSV output with configurable skill formatting
- JSON output
- Flexible column selection

Usage:
    from src.data import OutputHandler
    
    handler = OutputHandler(config)
    handler.write_all(df)
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OutputHandler:
    """
    Handle formatting and writing of extraction results.
    
    Supports multiple output formats (CSV, JSON) with
    configurable fields and formatting options.
    
    Usage:
        handler = OutputHandler(config)
        output_paths = handler.write_all(df)
    """
    
    def __init__(self, config):
        """
        Initialize output handler.
        
        Args:
            config: ConfigLoader instance
        """
        self.config = config
        self.output_dir = Path(config.get("output.directory", "data/processed"))
        self.formats = config.get("output.formats", ["csv"])
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def format_results(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format extraction results for output.
        
        Args:
            df: DataFrame with extraction results
            
        Returns:
            Formatted DataFrame
        """
        # Get configured output columns
        include_columns = self.config.get(
            "output.csv.include_columns",
            ['job_id', 'extracted_skills', 'skill_count']
        )
        
        # Build output DataFrame
        output_df = pd.DataFrame()
        
        for col in include_columns:
            if col in df.columns:
                output_df[col] = df[col]
            elif col == 'job_title':
                # Handle optional job title
                title_col = self.config.get("input.columns.title_column")
                if title_col and title_col in df.columns:
                    output_df['job_title'] = df[title_col]
                else:
                    output_df['job_title'] = ''
        
        return output_df
    
    def write_csv(self, df: pd.DataFrame) -> str:
        """
        Write results to CSV file.
        
        Args:
            df: DataFrame to write
            
        Returns:
            Path to written file
        """
        filename = self.config.get("output.csv.filename", "extracted_skills.csv")
        output_path = self.output_dir / filename
        
        # Get skills format
        skills_format = self.config.get("output.csv.skills_format", "comma_separated")
        
        # Prepare output DataFrame
        output_df = self.format_results(df)
        
        # Format skills column
        if 'extracted_skills' in output_df.columns:
            if skills_format == "comma_separated":
                output_df['extracted_skills'] = output_df['extracted_skills'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                )
            elif skills_format == "json_array":
                output_df['extracted_skills'] = output_df['extracted_skills'].apply(
                    lambda x: json.dumps(x) if isinstance(x, list) else str(x)
                )
        
        # Write to CSV
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Wrote CSV output: {output_path}")
        return str(output_path)
    
    def write_json(self, df: pd.DataFrame) -> str:
        """
        Write results to JSON file.
        
        Args:
            df: DataFrame to write
            
        Returns:
            Path to written file
        """
        filename = self.config.get("output.json.filename", "extracted_skills.json")
        output_path = self.output_dir / filename
        indent = self.config.get("output.json.indent", 2)
        
        # Prepare output DataFrame
        output_df = self.format_results(df)
        
        # Convert to records
        records = output_df.to_dict(orient='records')
        
        # Write to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=indent, ensure_ascii=False)
        
        logger.info(f"Wrote JSON output: {output_path}")
        return str(output_path)
    
    def write_all(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Write results in all configured formats.
        
        Args:
            df: DataFrame to write
            
        Returns:
            Dict mapping format to output path
        """
        output_paths = {}
        
        for fmt in self.formats:
            if fmt == "csv":
                output_paths['csv'] = self.write_csv(df)
            elif fmt == "json":
                output_paths['json'] = self.write_json(df)
            else:
                logger.warning(f"Unknown output format: {fmt}")
        
        return output_paths


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("OutputHandler module loaded successfully!")
    print("Use OutputHandler(config).write_all(df) to write results.")
