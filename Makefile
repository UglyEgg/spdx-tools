.PHONY: help install install-dev sync clean clean-all test test-cov lint format type-check pre-commit build publish docs serve-docs update-spdx-data run-example

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
install: ## Install the package in the current environment
	uv pip install -e .

install-dev: ## Install the package with development dependencies
	uv sync --dev

sync: ## Sync dependencies with uv.lock
	uv sync

sync-dev: ## Sync development dependencies
	uv sync --dev

# Cleaning targets
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete
	find . -type f -name "*.rej" -delete

clean-all: clean ## Clean everything including virtual environment
	rm -rf .venv/
	rm -rf .uv/
	rm -rf uv.lock

# Testing
test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

test-verbose: ## Run tests with verbose output
	uv run pytest -v

# Code quality
lint: ## Run linting checks
	uv run flake8 src tests
	uv run black --check src tests
	uv run isort --check-only src tests

format: ## Format code with black and isort
	uv run black src tests
	uv run isort src tests

type-check: ## Run type checking with mypy
	uv run mypy src

# Pre-commit
pre-commit-install: ## Install pre-commit hooks
	uv run --extra dev python -m pre_commit install

pre-commit: ## Run pre-commit on all files
	uv run --extra dev python -m pre_commit run --all-files

# Quality check combo
check: lint type-check test ## Run all quality checks

# Build and publish
build: clean ## Build the package
	uv build

publish-test: build ## Publish to TestPyPI
	uv publish --repository testpypi

publish: build ## Publish to PyPI
	uv publish

# Development utilities
update-spdx-data: ## Update the SPDX license data
	uv run python -m spdx_headers.generate_data

run-example: ## Run example usage of the tool
	@echo "Adding MIT headers to example files..."
	uv run spdx-headers --add MIT --dry-run

list-licenses: ## List all available SPDX licenses
	uv run spdx-headers --list

verify-headers: ## Verify SPDX headers in the project
	uv run spdx-headers --verify

check-headers: ## Check for missing headers (CI-friendly)
	uv run spdx-headers --check

# Documentation (if you add docs later)
docs: ## Build documentation
	@echo "Documentation target - implement when adding docs"

serve-docs: ## Serve documentation locally
	@echo "Documentation serving target - implement when adding docs"

# Development workflow shortcuts
dev-setup: install-dev pre-commit-install update-spdx-data ## Complete development setup
	@echo "Development environment is ready!"
	@echo "Run 'make help' to see available commands"

quick-check: format lint test ## Quick development check (format, lint, test)

release-check: clean check build ## Full release preparation check

# Environment info
info: ## Show environment information
	@echo "Python version:"
	@uv run python --version
	@echo "\nUV version:"
	@uv --version
	@echo "\nInstalled packages:"
	@uv pip list
	@echo "\nProject info:"
	@uv run python -c "import spdx_tools; print(f'spdx-tools location: {spdx_tools.__file__}')" 2>/dev/null || echo "spdx-tools not installed"

# Dependency management
update-deps: ## Update all dependencies
	uv sync --upgrade

lock: ## Generate/update uv.lock file
	uv lock

# CI/CD helpers
ci-install: ## Install for CI environment
	uv sync --frozen

ci-test: ## Run tests in CI mode
	uv run pytest --cov=src --cov-report=xml

ci-check: ## Run all CI checks
	uv run black --check src tests
	uv run isort --check-only src tests
	uv run flake8 src tests
	uv run mypy src
	uv run pytest --cov=src --cov-report=xml

# Utility targets
show-outdated: ## Show outdated dependencies
	uv pip list --outdated

tree: ## Show project structure
	tree -I '__pycache__|*.pyc|*.pyo|.git|.pytest_cache|.mypy_cache|*.egg-info|build|dist|.venv|.uv'

# Example workflows
example-add-headers: ## Example: Add GPL-3.0-only headers
	uv run spdx-headers --add GPL-3.0-only --dry-run

example-change-license: ## Example: Change to MIT license
	uv run spdx-headers --change MIT --dry-run

example-extract-license: ## Example: Extract license file
	uv run spdx-headers --add Apache-2.0 --extract --dry-run
