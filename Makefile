# Configure runtime paths
export UV_CACHE_DIR := $(CURDIR)/.uv-cache

PYTHON := $(CURDIR)/.venv/bin/python

# Configure template defaults for this project
RUN := $(PYTHON) -m
RUN_DEV := $(PYTHON) -m
PYTEST_COV_ARGS := --cov=src --cov-report=html --cov-report=term-missing
LINT_PATHS := src tests
FORMAT_PATHS := src tests
CLEAN_FIND_EXTS := pyc pyo orig rej
CLEAN_CACHE_DIRS := .pytest_cache .mypy_cache .tox htmlcov .coverage .ruff_cache
CLEAN_ALL_EXTRA := .uv uv.lock
TYPECHECK_PATHS := src
PRE_COMMIT := pre_commit

MARKDOWNLINT_HOOK := markdownlint-cli2

# Indicate which template targets are overridden locally
TEMPLATE_SKIP_install := 1
TEMPLATE_SKIP_install_dev := 1
TEMPLATE_SKIP_info := 1

# Load shared template definitions
include Makefile.template

LINT_COMMANDS := \
    $(RUN_DEV) $(RUFF) $(RUFF_ARGS) && \
    $(RUN_DEV) $(BLACK) $(BLACK_LINT_ARGS) && \
    $(RUN_DEV) $(ISORT) $(ISORT_LINT_ARGS) && \
    $(RUN_DEV) $(PRE_COMMIT) run $(MARKDOWNLINT_HOOK) --all-files

.PHONY: sync sync-dev build publish publish-test serve-docs update-spdx-data bump-version list-licenses verify-headers check-headers dev-setup quick-check release-check info update-deps lock ci-install ci-test ci-check show-outdated tree lint-markdown lint-markdown-summary

# Environment setup
install: ## Install the package in the current environment
	uv pip install -e .

install-dev: ## Install the package with development dependencies
	uv sync --extra dev

sync: ## Sync dependencies with uv.lock
	uv sync

sync-dev: ## Sync development dependencies
	uv sync --extra dev

bump-version: ## Bump the project version (usage: make bump-version part=patch|minor|major or version=X.Y.Z)
	@if [ -n "$(version)" ]; then \
		uv run --extra dev python scripts/bump_version.py --set $(version); \
	else \
		uv run --extra dev python scripts/bump_version.py --part $${part:-patch}; \
	fi
	@uv run --extra dev hatch version

# Build and publish
build: clean ## Build the package
	./scripts/build.sh

publish-test: ## Build and publish to TestPyPI
	./scripts/release.sh --repository testpypi

publish: ## Build and publish to PyPI
	./scripts/release.sh

# Environment info
info: ## Show environment information
	@echo "Python version:"
	@$(PYTHON) --version
	@if command -v uv >/dev/null 2>&1; then \
		echo; \
		echo "UV version:"; \
		uv --version; \
		echo; \
		echo "Installed packages (uv pip list):"; \
		uv pip list; \
	else \
		echo; \
		echo "UV not found on PATH – skipping uv diagnostics."; \
	fi
	@echo
	@echo "Project info:"
	@PYTHONPATH=src $(PYTHON) -c "import importlib.util; spec = importlib.util.find_spec('spdx_headers'); print(f'spdx_headers module: {spec.origin}' if spec and spec.origin else 'spdx_headers not installed')"

# Development utilities
update-spdx-data: ## Update the SPDX license data
	uv run python -m spdx_headers.generate_data

list-licenses: ## List all available SPDX licenses
	@if [ ! -f src/spdx_headers/_version.py ]; then \
		echo "Error: src/spdx_headers/_version.py is missing."; \
		echo "Run \`python scripts/bump_version.py --set <version>\` to regenerate it."; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m spdx_headers.cli --list

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

# Custom markdown linting target
lint-markdown: ## Run markdown linting (formats: compact, grouped, detailed, summary)
	@./scripts/lint-markdown.sh $(FORMAT)

lint-markdown-summary: ## Run markdown linting summary (formats: table, stats, tree, quick)
	@./scripts/lint-markdown-summary.sh $(FORMAT)
