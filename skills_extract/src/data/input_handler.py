"""
Input Handler for CSV and Excel Files

Tasks: T2.1 - T2.6

This module provides:
- CSV loading with auto-encoding detection
- Excel file loading
- Dynamic column validation
- Auto-generation of row IDs
- Chunked loading for large files

Usage:
    from src.data import InputHandler
    
    handler = InputHandler(config)
    df = handler.load_file()
"""

import chardet
import pandas as pd
from pathlib import Path
from typing import Iterator, Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InputError(Exception):
    """Raised when input loading or validation fails."""
    pass


class InputHandler:
    """
    Handle loading and validation of input data files.
    
    Supports CSV and Excel formats with automatic type detection.
    Designed to be dataset-agnostic through configuration-driven
    column mapping.
    
    Usage:
        handler = InputHandler(config)
        df = handler.load_file()
        
        # For large files
        for chunk in handler.load_file_chunked():
            process(chunk)
    """
    
    SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls'}
    
    def __init__(self, config):
        """
        Initialize with configuration.
        
        Args:
            config: ConfigLoader instance with input settings
        """
        self.config = config
        self.file_path = config.get("input.file_path")
        self.file_type = config.get("input.file_type", "auto")
        self.encoding = config.get("input.encoding", "auto")
        self.chunk_size = config.get("input.chunk_size", 5000)
        
        # Column configuration
        self.text_column = config.get("input.columns.text_column")
        self.id_column = config.get("input.columns.id_column")
        self.title_column = config.get("input.columns.title_column")
        self.id_prefix = config.get("input.id_prefix", "jd")
    
    def load_file(self) -> pd.DataFrame:
        """
        Load data from configured file path.
        
        Returns:
            DataFrame with loaded data
            
        Raises:
            InputError: If file not found or format unsupported
        """
        path = Path(self.file_path)
        
        if not path.exists():
            raise InputError(
                f"Input file not found: {self.file_path}\n"
                f"Please check the file path in your config."
            )
        
        # Detect file type
        if self.file_type == "auto":
            file_type = self._detect_file_type(self.file_path)
        else:
            file_type = self.file_type
        
        # Load based on type
        if file_type == "csv":
            df = self._load_csv(self.file_path)
        else:
            df = self._load_excel(self.file_path)
        
        # Validate columns
        self.validate_columns(df)
        
        # Add row IDs
        df = self.add_row_ids(df)
        
        return df
    
    def load_file_chunked(self) -> Iterator[pd.DataFrame]:
        """
        Load large file in chunks for memory efficiency.
        
        Yields:
            DataFrame chunks of configured size
        """
        path = Path(self.file_path)
        
        if not path.exists():
            raise InputError(f"Input file not found: {self.file_path}")
        
        file_type = self._detect_file_type(self.file_path)
        
        logger.info(f"Loading file in chunks of {self.chunk_size} rows")
        
        if file_type == "csv":
            yield from self._load_csv_chunked(self.file_path)
        else:
            # Excel doesn't support native chunking, load and split
            yield from self._load_excel_chunked(self.file_path)
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to input file
            
        Returns:
            File type string ('csv' or 'xlsx')
        """
        suffix = Path(file_path).suffix.lower()
        
        if suffix not in self.SUPPORTED_FORMATS:
            raise InputError(
                f"Unsupported file format: {suffix}\n"
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )
        
        return 'csv' if suffix == '.csv' else 'xlsx'
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding using chardet.
        
        Args:
            file_path: Path to file
            
        Returns:
            Detected encoding string
        """
        # Read sample of file for detection
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Sample first 10KB
        
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        
        logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.2%})")
        
        # Fall back to utf-8 if detection uncertain
        if confidence < 0.7:
            logger.warning(
                f"Low confidence in encoding detection ({confidence:.2%}). "
                f"Falling back to UTF-8."
            )
            return 'utf-8'
        
        return encoding
    
    def _load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load CSV file with encoding handling.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Loaded DataFrame
        """
        # Determine encoding
        if self.encoding == "auto":
            encoding = self._detect_encoding(file_path)
        else:
            encoding = self.encoding
        
        logger.info(f"Loading CSV: {file_path} (encoding: {encoding})")
        
        try:
            df = pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            # Try common fallback encodings
            fallback_encodings = ['utf-8', 'latin-1', 'cp1252']
            for enc in fallback_encodings:
                try:
                    logger.warning(f"Retrying with {enc} encoding")
                    df = pd.read_csv(file_path, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise InputError(
                    f"Could not decode file with any encoding: {file_path}"
                )
        
        logger.info(f"Loaded {len(df)} rows from CSV")
        return df
    
    def _load_csv_chunked(self, file_path: str) -> Iterator[pd.DataFrame]:
        """
        Load CSV in chunks using pandas chunked reader.
        """
        encoding = (
            self._detect_encoding(file_path) 
            if self.encoding == "auto" 
            else self.encoding
        )
        
        chunk_iter = pd.read_csv(
            file_path,
            encoding=encoding,
            chunksize=self.chunk_size
        )
        
        for i, chunk in enumerate(chunk_iter):
            logger.debug(f"Processing chunk {i+1} ({len(chunk)} rows)")
            self.validate_columns(chunk)
            yield self.add_row_ids(chunk, offset=i * self.chunk_size)
    
    def _load_excel(self, file_path: str) -> pd.DataFrame:
        """
        Load Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Loaded DataFrame
        """
        # Get sheet configuration (default to first sheet)
        sheet_name = self.config.get("input.excel.sheet_name", 0)
        
        logger.info(f"Loading Excel: {file_path} (sheet: {sheet_name})")
        
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                engine='openpyxl'
            )
        except Exception as e:
            raise InputError(f"Failed to load Excel file: {e}")
        
        logger.info(f"Loaded {len(df)} rows from Excel")
        return df
    
    def _load_excel_chunked(self, file_path: str) -> Iterator[pd.DataFrame]:
        """
        Load Excel and yield in chunks (Excel doesn't support streaming).
        """
        # Must load entire file first (Excel limitation)
        df = self._load_excel(file_path)
        self.validate_columns(df)
        
        # Split into chunks
        for start in range(0, len(df), self.chunk_size):
            end = start + self.chunk_size
            chunk = df.iloc[start:end].copy()
            
            logger.debug(f"Yielding rows {start} to {min(end, len(df))}")
            yield self.add_row_ids(chunk, offset=start)
    
    def validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate required columns exist in DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            InputError: If required column is missing
        """
        available_columns = list(df.columns)
        
        # Check required text column
        if self.text_column not in df.columns:
            raise InputError(
                f"Text column '{self.text_column}' not found in data.\n"
                f"Available columns: {available_columns}\n"
                f"Please update 'input.columns.text_column' in config."
            )
        
        # Check optional columns if specified
        if self.id_column and self.id_column not in df.columns:
            raise InputError(
                f"ID column '{self.id_column}' not found in data.\n"
                f"Available columns: {available_columns}\n"
                f"Set 'input.columns.id_column' to null for auto-generation."
            )
        
        if self.title_column and self.title_column not in df.columns:
            logger.warning(
                f"Title column '{self.title_column}' not found. "
                f"Job titles will be empty."
            )
        
        logger.debug(f"Column validation passed. Using text column: {self.text_column}")
    
    def add_row_ids(self, df: pd.DataFrame, offset: int = 0) -> pd.DataFrame:
        """
        Add or validate row IDs.
        
        If id_column is specified in config, use that column.
        Otherwise, generate sequential IDs.
        
        Args:
            df: DataFrame to add IDs to
            offset: Starting offset for sequential IDs (for chunked loading)
            
        Returns:
            DataFrame with 'job_id' column
        """
        df = df.copy()  # Don't modify original
        
        if self.id_column and self.id_column in df.columns:
            # Use existing ID column
            df['job_id'] = df[self.id_column].astype(str)
            logger.debug(f"Using existing ID column: {self.id_column}")
        else:
            # Generate sequential IDs
            num_digits = max(len(str(len(df) + offset)), 3)  # At least 3 digits
            
            df['job_id'] = [
                f"{self.id_prefix}_{str(i + offset + 1).zfill(num_digits)}"
                for i in range(len(df))
            ]
            logger.info(f"Generated {len(df)} sequential IDs (prefix: {self.id_prefix})")
        
        # Verify uniqueness
        if df['job_id'].duplicated().any():
            duplicate_count = df['job_id'].duplicated().sum()
            logger.warning(f"Found {duplicate_count} duplicate IDs")
        
        return df
    
    def should_use_chunking(self) -> bool:
        """
        Determine if file should be loaded in chunks.
        
        Uses file size as heuristic (> threshold suggests chunking).
        """
        path = Path(self.file_path)
        
        if not path.exists():
            return False
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        threshold_mb = self.config.get("input.chunk_threshold_mb", 100)
        
        if file_size_mb > threshold_mb:
            logger.info(
                f"File size ({file_size_mb:.1f}MB) exceeds threshold. "
                f"Using chunked loading."
            )
            return True
        
        return False
    
    def get_row_count_estimate(self) -> Optional[int]:
        """
        Get estimated row count without loading entire file.
        
        Returns:
            Estimated row count or None if cannot determine
        """
        path = Path(self.file_path)
        
        if not path.exists():
            return None
        
        if path.suffix.lower() == '.csv':
            # Count lines in CSV (approximate)
            with open(path, 'rb') as f:
                return sum(1 for _ in f) - 1  # Subtract header
        
        return None


# =============================================================================
# Quick Test
# =============================================================================
if __name__ == "__main__":
    print("InputHandler module loaded successfully!")
    print("Use InputHandler(config).load_file() to load data.")
