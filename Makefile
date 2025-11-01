# Configure template defaults for this project
RUN := uv run
RUN_DEV := uv run --extra dev
PYTEST_COV_ARGS := --cov=src --cov-report=html --cov-report=term-missing
LINT_PATHS := src tests
FORMAT_PATHS := src tests
CLEAN_FIND_EXTS := pyc pyo orig rej
CLEAN_CACHE_DIRS := .pytest_cache .mypy_cache .tox htmlcov .coverage .ruff_cache
CLEAN_ALL_EXTRA := .uv uv.lock
TYPECHECK_PATHS := src
PRE_COMMIT := python -m pre_commit

# Indicate which template targets are overridden locally
TEMPLATE_SKIP_install := 1
TEMPLATE_SKIP_install_dev := 1

# Load shared template definitions
include MAKEFILE.template

.PHONY: sync sync-dev build publish publish-test serve-docs update-spdx-data bump-version list-licenses verify-headers check-headers dev-setup quick-check release-check info update-deps lock ci-install ci-test ci-check show-outdated tree example-add-headers example-change-license example-extract-license

# Environment setup
install: ## Install the package in the current environment
	uv pip install -e .

install-dev: ## Install the package with development dependencies
	uv sync --dev

sync: ## Sync dependencies with uv.lock
	uv sync

sync-dev: ## Sync development dependencies
	uv sync --dev

bump-version: ## Bump the project version (usage: make bump-version part=patch|minor|major or version=X.Y.Z)
	@if [ -n "$(version)" ]; then \
		uv run --extra dev python scripts/bump_version.py --set $(version); \
	else \
		uv run --extra dev python scripts/bump_version.py --part $${part:-patch}; \
	fi
	@uv run --extra dev hatch version

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

list-licenses: ## List all available SPDX licenses
	uv run spdx-headers --list

verify-headers: ## Verify SPDX headers in the project
	uv run spdx-headers --verify

check-headers: ## Check for missing headers (CI-friendly)
	uv run spdx-headers --check

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
	@echo -e "\nUV version:"
	@uv --version
	@echo -e "\nInstalled packages:"
	@uv pip list
	@echo -e "\nProject info:"
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
	uv run ruff check src tests
	uv run mypy src
	uv run pytest --cov=src --cov-report=xml

# Utility targets
show-outdated: ## Show outdated dependencies
	uv pip list --outdated

tree: ## Show project structure
	tree -I '__pycache__|*.pyc|*.pyo|.git|.pytest_cache|.mypy_cache|*.egg-info|build|dist|.venv|.uv'

# Example workflows
example-add-headers: ## Example: Add AGPL-3.0-or-later headers
	uv run spdx-headers --add AGPL-3.0-or-later --dry-run

example-change-license: ## Example: Change to MIT license
	uv run spdx-headers --change MIT --dry-run

example-extract-license: ## Example: Extract license file
	uv run spdx-headers --add Apache-2.0 --extract --dry-run
