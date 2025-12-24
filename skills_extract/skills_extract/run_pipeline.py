#!/usr/bin/env python
"""
Skills Extraction Pipeline

Main entry point for running the full extraction pipeline.

Usage:
    python run_pipeline.py --config src/config/config.yaml
    python run_pipeline.py --config src/config/config.yaml --verbose
    python run_pipeline.py --config src/config/config.yaml --dry-run

Based on Cookiecutter Data Science project structure.
"""

import argparse
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ConfigLoader, ConfigurationError
from src.utils import setup_logging_from_config, get_logger
from src.data import InputHandler, InputError, OutputHandler
from src.features import Preprocessor, SkillDictionary, SkillExtractor
from src.features import Aggregator, RulesGenerator
from src.visualization import AnalyticsGenerator


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract skills from job descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --config src/config/config.yaml
  python run_pipeline.py --config src/config/config.yaml --verbose
  python run_pipeline.py --config src/config/config.yaml --dry-run
        """
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate config and exit without processing'
    )
    parser.add_argument(
        '--analytics',
        action='store_true',
        help='Generate analytics output (Phase 2)'
    )
    parser.add_argument(
        '--rules',
        action='store_true',
        help='Generate rules output (Phase 2)'
    )
    
    return parser.parse_args()


def run_pipeline(
    config_path: str, 
    verbose: bool = False, 
    dry_run: bool = False,
    generate_analytics: bool = False,
    generate_rules: bool = False
):
    """
    Run the full extraction pipeline.
    
    Args:
        config_path: Path to configuration file
        verbose: Enable debug logging
        dry_run: Only validate config, don't process
        generate_analytics: Generate analytics output
        generate_rules: Generate rules output
    """
    # Step 1: Load configuration
    print(f"Loading configuration from: {config_path}")
    try:
        config = ConfigLoader.load(config_path)
    except ConfigurationError as e:
        print(f"❌ Configuration error:\n{e}")
        sys.exit(1)
    
    # Override log level if verbose
    if verbose:
        config._config.setdefault('logging', {})['level'] = 'DEBUG'
    
    # Step 2: Setup logging
    setup_logging_from_config(config)
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Skills Extraction Pipeline Started")
    logger.info("=" * 60)
    logger.info(f"Configuration: {config}")
    
    # Dry run - just validate
    if dry_run:
        logger.info("✅ Dry run mode - configuration valid")
        print("\n✅ Configuration is valid!")
        return
    
    try:
        # Step 3: Load input data
        logger.info("Step 1/5: Loading input data...")
        input_handler = InputHandler(config)
        df = input_handler.load_file()
        logger.info(f"Loaded {len(df)} records")
        
        # Step 4: Preprocess text
        logger.info("Step 2/5: Preprocessing text...")
        preprocessor = Preprocessor(config)
        text_column = config.get("input.columns.text_column")
        df, preprocess_stats = preprocessor.preprocess(df, text_column)
        
        # Step 5: Load skill dictionaries
        logger.info("Step 3/5: Loading skill dictionaries...")
        dictionary = SkillDictionary(config)
        dictionary.load_all()
        
        # Step 6: Extract skills
        logger.info("Step 4/5: Extracting skills...")
        extractor = SkillExtractor(config, dictionary)
        df = extractor.extract_batch(df, 'processed_text')
        
        # Step 7: Write outputs
        logger.info("Step 5/5: Writing outputs...")
        output_handler = OutputHandler(config)
        output_paths = output_handler.write_all(df)
        
        # Optional: Generate analytics (Phase 2)
        if generate_analytics or config.get("analytics.enabled", False):
            logger.info("Generating analytics...")
            analytics_generator = AnalyticsGenerator(config)
            analytics_paths = analytics_generator.generate_all(df)
            output_paths['analytics'] = analytics_paths
        
        # Optional: Generate rules (Phase 2)
        if generate_rules or config.get("rules.enabled", False):
            logger.info("Generating rules...")
            rules_generator = RulesGenerator(config, dictionary)
            rules_paths = rules_generator.generate_all(df)
            output_paths['rules'] = rules_paths
        
        # Step 8: Report summary
        extraction_stats = extractor.get_extraction_stats()
        
        logger.info("=" * 60)
        logger.info("✅ Pipeline Complete!")
        logger.info("=" * 60)
        logger.info(f"Records processed: {len(df)}")
        logger.info(f"Records skipped (null/empty): {preprocess_stats['skipped_null'] + preprocess_stats['skipped_empty']}")
        logger.info(f"Total skills extracted: {df['skill_count'].sum()}")
        logger.info(f"Unique skills found: {extraction_stats['unique_skills_count']}")
        logger.info(f"Average skills per JD: {df['skill_count'].mean():.1f}")
        logger.info(f"Output files: {output_paths}")
        
        print("\n" + "=" * 60)
        print("✅ Pipeline Complete!")
        print("=" * 60)
        print(f"Records processed: {len(df)}")
        print(f"Total skills extracted: {df['skill_count'].sum()}")
        print(f"Output files:")
        for fmt, path in output_paths.items():
            if isinstance(path, dict):
                print(f"  {fmt}: {len(path)} files")
            else:
                print(f"  {fmt}: {path}")
        
    except InputError as e:
        logger.error(f"Input error: {e}")
        print(f"\n❌ Input error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    args = parse_args()
    run_pipeline(
        args.config, 
        args.verbose, 
        args.dry_run,
        args.analytics,
        args.rules
    )


if __name__ == "__main__":
    main()
