"""
Text Preprocessor for Job Descriptions

Tasks: T3.1 - T3.4

This module provides:
- Text cleaning and normalization
- Whitespace handling
- Special character removal (preserving skill-relevant chars)
- Abbreviation expansion
- Null/empty value handling

Usage:
    from src.features import Preprocessor
    
    preprocessor = Preprocessor(config)
    df, stats = preprocessor.preprocess(df, text_column='description')
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Tuple, Optional
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Preprocessor:
    """
    Preprocess job description text for skill extraction.
    
    Provides configurable text cleaning and normalization
    while preserving skill-relevant information.
    
    Usage:
        preprocessor = Preprocessor(config)
        df, stats = preprocessor.preprocess(df, text_column='description')
    """
    
    def __init__(self, config):
        """
        Initialize with preprocessing configuration.
        
        Args:
            config: ConfigLoader instance
        """
        self.config = config
        
        # Load settings from config
        self.lowercase = config.get("preprocessing.lowercase", True)
        self.normalize_whitespace = config.get("preprocessing.normalize_whitespace", True)
        self.remove_special_chars = config.get("preprocessing.remove_special_chars", True)
        self.preserve_hyphens = config.get("preprocessing.preserve_hyphens", True)
        self.expand_abbreviations = config.get("preprocessing.expand_abbreviations", False)
        
        # Load abbreviation mappings if enabled
        self.abbreviations = {}
        if self.expand_abbreviations:
            self._load_abbreviations()
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'skipped_null': 0,
            'skipped_empty': 0
        }
    
    def _load_abbreviations(self) -> None:
        """Load abbreviation mappings from config file."""
        abbreviations_file = self.config.get("preprocessing.abbreviations_file")
        
        if not abbreviations_file:
            logger.warning("Abbreviations enabled but no file specified")
            return
        
        path = Path(abbreviations_file)
        if not path.exists():
            logger.warning(f"Abbreviations file not found: {abbreviations_file}")
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.abbreviations = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded {len(self.abbreviations)} abbreviation mappings")
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse abbreviations file: {e}")
    
    def preprocess(
        self, 
        df: pd.DataFrame, 
        text_column: str
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Run preprocessing pipeline on DataFrame.
        
        Args:
            df: DataFrame containing text to preprocess
            text_column: Name of column containing text
            
        Returns:
            Tuple of (processed DataFrame, statistics dict)
        """
        df = df.copy()
        
        # Track which rows to keep
        valid_mask = self._create_valid_mask(df, text_column)
        
        # Log skipped rows
        skipped_df = df[~valid_mask]
        self._log_skipped_rows(skipped_df)
        
        # Filter to valid rows
        df = df[valid_mask].copy()
        
        # Apply preprocessing
        df['processed_text'] = df[text_column].apply(self._preprocess_text)
        
        self._stats['total_processed'] = len(df)
        
        logger.info(
            f"Preprocessing complete: {self._stats['total_processed']} processed, "
            f"{self._stats['skipped_null']} null, "
            f"{self._stats['skipped_empty']} empty"
        )
        
        return df, self._stats.copy()
    
    def _preprocess_text(self, text: str) -> str:
        """
        Apply all preprocessing steps to a single text.
        
        Pipeline order matters:
        1. Clean (remove unwanted elements)
        2. Normalize (standardize format)
        3. Expand abbreviations
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Step 1: Clean
        text = self._clean(text)
        
        # Step 2: Normalize
        text = self._normalize(text)
        
        # Step 3: Expand abbreviations
        if self.expand_abbreviations and self.abbreviations:
            text = self._expand_abbreviations(text)
        
        return text
    
    def _clean(self, text: str) -> str:
        """
        Remove unwanted characters while preserving skill-relevant info.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', ' ', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' ', text)
        
        if self.remove_special_chars:
            if self.preserve_hyphens:
                # Keep hyphens, periods, and plus signs (C++, .NET, Vue.js)
                # Also keep # for C#
                text = re.sub(r'[^\w\s\-\.\+#]', ' ', text)
            else:
                # Remove all special characters
                text = re.sub(r'[^\w\s]', ' ', text)
        
        return text
    
    def _normalize(self, text: str) -> str:
        """
        Normalize text format.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Lowercase
        if self.lowercase:
            text = text.lower()
        
        # Normalize whitespace
        if self.normalize_whitespace:
            # Replace multiple spaces/tabs/newlines with single space
            text = re.sub(r'\s+', ' ', text)
            # Strip leading/trailing whitespace
            text = text.strip()
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """
        Expand abbreviations in text.
        
        Uses word boundaries to avoid partial matches.
        
        Args:
            text: Text with potential abbreviations
            
        Returns:
            Text with abbreviations expanded
        """
        for abbrev, expansion in self.abbreviations.items():
            # Use word boundaries for whole-word matching
            # Case-insensitive matching
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def _create_valid_mask(self, df: pd.DataFrame, text_column: str) -> pd.Series:
        """
        Create boolean mask identifying valid (processable) rows.
        
        Args:
            df: DataFrame to check
            text_column: Name of text column
            
        Returns:
            Boolean Series (True = valid row)
        """
        # Check for null values
        null_mask = df[text_column].isna()
        self._stats['skipped_null'] = null_mask.sum()
        
        # Check for empty strings (after stripping)
        empty_mask = df[text_column].fillna('').astype(str).str.strip() == ''
        self._stats['skipped_empty'] = (empty_mask & ~null_mask).sum()
        
        # Valid = not null AND not empty
        valid_mask = ~null_mask & ~empty_mask
        
        return valid_mask
    
    def _log_skipped_rows(self, df: pd.DataFrame) -> None:
        """
        Log information about skipped rows for debugging.
        
        Args:
            df: DataFrame containing skipped rows
        """
        if len(df) == 0:
            return
        
        # Log sample of skipped row IDs
        if 'job_id' in df.columns:
            skipped_ids = df['job_id'].head(10).tolist()
            logger.warning(
                f"Skipped {len(df)} rows with null/empty text. "
                f"Sample IDs: {skipped_ids}"
            )
        else:
            skipped_indices = df.index[:10].tolist()
            logger.warning(
                f"Skipped {len(df)} rows with null/empty text. "
                f"Sample indices: {skipped_indices}"
            )
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get preprocessing statistics."""
        return self._stats.copy()


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("Preprocessor module loaded successfully!")
    print("Use Preprocessor(config).preprocess(df, text_column) to preprocess data.")
