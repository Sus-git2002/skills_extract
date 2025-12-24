# Skills Extraction Pipeline

A production-grade, dataset-agnostic pipeline for extracting skills from job descriptions.

## Project Organization

```
├── LICENSE
├── Makefile           <- Makefile with commands like `make extract` or `make test`
├── README.md          <- The top-level README for developers using this project
├── data
│   ├── external       <- Data from third party sources (skill dictionaries)
│   ├── interim        <- Intermediate data that has been transformed
│   ├── processed      <- The final, canonical data sets (extracted skills)
│   └── raw            <- The original, immutable data dump (job descriptions)
│
├── docs               <- Documentation and implementation guides
│
├── models             <- Trained models (for future ML-based extraction)
│
├── notebooks          <- Jupyter notebooks for exploration and analysis
│                         Naming: `1.0-initials-description.ipynb`
│
├── references         <- Data dictionaries, skill lists, and explanatory materials
│   └── dictionaries   <- Skill dictionary files (technical, soft, variations)
│
├── reports            <- Generated analysis as HTML, PDF, JSON, etc.
│   ├── figures        <- Generated graphics and figures
│   ├── analytics      <- Skill analytics JSON files
│   └── rules          <- Extraction rules JSONL files
│
├── requirements.txt   <- The requirements file for reproducing the environment
│
├── setup.py           <- Makes project pip installable (`pip install -e .`)
│
├── src                <- Source code for use in this project
│   ├── __init__.py    <- Makes src a Python module
│   │
│   ├── config         <- Configuration management
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── config.yaml
│   │
│   ├── data           <- Scripts to download, load, or generate data
│   │   ├── __init__.py
│   │   ├── input_handler.py    <- Load CSV/Excel files
│   │   └── output_handler.py   <- Write extraction results
│   │
│   ├── features       <- Scripts to turn raw data into features/extractions
│   │   ├── __init__.py
│   │   ├── preprocessor.py     <- Text cleaning and normalization
│   │   ├── skill_dictionary.py <- Dictionary loading and management
│   │   ├── skill_extractor.py  <- Core extraction logic
│   │   ├── aggregator.py       <- Analytics aggregation
│   │   └── rules_generator.py  <- Rules export
│   │
│   ├── models         <- Scripts for ML-based extraction (future)
│   │   └── __init__.py
│   │
│   ├── visualization  <- Scripts for analytics and reporting
│   │   ├── __init__.py
│   │   └── analytics_generator.py
│   │
│   └── utils          <- Utility functions
│       ├── __init__.py
│       └── logger.py
│
├── tests              <- Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_input_handler.py
│   ├── test_preprocessor.py
│   ├── test_skill_extractor.py
│   └── test_integration.py
│
└── run_pipeline.py    <- Main entry point for running the pipeline
```

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd skills_extraction_pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Or just install dependencies
pip install -r requirements.txt
```

### 2. Configure

Edit `src/config/config.yaml` to set your input file and column mappings:

```yaml
input:
  file_path: "data/raw/job_descriptions.csv"
  columns:
    text_column: "your_description_column"  # Required
    id_column: null  # Optional, auto-generates if null
```

### 3. Run

```bash
# Using make
make extract

# Or directly
python run_pipeline.py --config src/config/config.yaml

# With verbose logging
python run_pipeline.py --config src/config/config.yaml --verbose

# Validate config only (dry run)
python run_pipeline.py --config src/config/config.yaml --dry-run
```

### 4. Output

Results are saved to:
- `data/processed/extracted_skills.csv` - Tabular results
- `data/processed/extracted_skills.json` - Structured JSON
- `reports/pipeline.log` - Execution log
- `reports/analytics/` - Skill analytics (Phase 2)
- `reports/rules/` - Extraction rules (Phase 2)

## Make Commands

```bash
make requirements    # Install Python dependencies
make data           # Process raw data
make extract        # Run the full extraction pipeline
make test           # Run test suite
make lint           # Lint using flake8
make clean          # Delete compiled Python files
```

## Adding Custom Skills

1. Create a text file with skills (one per line)
2. Place in `references/dictionaries/`
3. Update config:
   ```yaml
   extraction:
     dictionaries:
       custom: "references/dictionaries/my_custom_skills.txt"
   ```

## Development

```bash
# Run tests
make test

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Format code
black src/
isort src/
```

## Project Features

- **Multiple Input Formats**: CSV and Excel with auto-encoding detection
- **Config-Driven**: All behavior controlled via YAML configuration
- **Skill Normalization**: Map variations to canonical names (JS → JavaScript)
- **Multiple Output Formats**: CSV, JSON, JSONL
- **Production-Ready**: Comprehensive logging, testing, and error handling
- **Extensible**: Designed for future ML-based extraction strategies

## License

[Your License]

---

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>.</small></p>
