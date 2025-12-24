.PHONY: clean data lint requirements test extract help

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = skills_extraction_pipeline
PYTHON_INTERPRETER = python3
CONFIG_FILE = src/config/config.yaml

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

## Lint using flake8
lint:
	flake8 src/
	flake8 tests/

## Format code using black and isort
format:
	black src/ tests/
	isort src/ tests/

## Run tests
test:
	pytest tests/ -v

## Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

## Run the full extraction pipeline
extract:
	$(PYTHON_INTERPRETER) run_pipeline.py --config $(CONFIG_FILE)

## Run pipeline with verbose logging
extract-verbose:
	$(PYTHON_INTERPRETER) run_pipeline.py --config $(CONFIG_FILE) --verbose

## Validate configuration only (dry run)
validate:
	$(PYTHON_INTERPRETER) run_pipeline.py --config $(CONFIG_FILE) --dry-run

## Process raw data (placeholder for data preparation)
data:
	@echo "Processing raw data..."
	@echo "Place your job description files in data/raw/"

## Generate analytics (Phase 2)
analytics:
	$(PYTHON_INTERPRETER) run_pipeline.py --config $(CONFIG_FILE) --analytics

## Set up python interpreter environment
create_environment:
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, creating conda environment."
	conda create --name $(PROJECT_NAME) python=3.10
	@echo ">>> New conda env created. Activate with:\nconda activate $(PROJECT_NAME)"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv
	@echo ">>> Installing virtualenv if not already installed.\nMake sure the following is in your PATH:"
	@echo ">>> Creating virtualenv in .venv/"
	$(PYTHON_INTERPRETER) -m venv .venv
	@echo ">>> New virtualenv created. Activate with:\nsource .venv/bin/activate"
endif

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Make Dataset - Copy raw data to processed
data/processed/extracted_skills.csv: data/raw/*.csv
	$(PYTHON_INTERPRETER) run_pipeline.py --config $(CONFIG_FILE)

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^)}##/:
# 	* save line in hold space
# 	* move to next line
# 	* exchange to hold space
# 	* get matched substring
# 	* print it
# )/## /:
# 	* save line in hold space
# 	* move to next line
# 	* exchange to hold space
# 	* get matched substring
# 	* print it
help:
	@echo "$$(tput bold)Available commands:$$(tput sgr0)"
	@echo
	@sed -n 's/^##//p' $(MAKEFILE_LIST) | column -t -s ':' | sed -e 's/^/  /'
