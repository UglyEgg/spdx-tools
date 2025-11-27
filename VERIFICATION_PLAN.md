# Verification Plan for Make Functions and Support Scripts

## Overview
This document outlines the verification plan for all make functions and support scripts, with special focus on version bumping and PyPI wheel building.

## Scripts to Verify

### 1. Version Bumping (`scripts/bump_version.py`)
**Purpose:** Automate version bumps by updating CHANGELOG.md and _version.py

**Key Functions:**
- Parse CHANGELOG.md to find current version
- Bump version (patch/minor/major or explicit)
- Update CHANGELOG.md with new release section
- Generate/update _version.py file
- Update comparison links in CHANGELOG.md

**Test Cases:**
1. ✅ Bump patch version (1.0.1 → 1.0.2)
2. ✅ Bump minor version (1.0.1 → 1.1.0)
3. ✅ Bump major version (1.0.1 → 2.0.0)
4. ✅ Set explicit version (1.0.1 → 1.5.0)
5. ✅ Verify _version.py generation
6. ✅ Verify CHANGELOG.md updates
7. ✅ Verify link updates

### 2. Build Script (`scripts/build.sh`)
**Purpose:** Build source distribution and wheel for PyPI

**Key Functions:**
- Extract version from _version.py
- Clean previous builds
- Build source distribution (.tar.gz)
- Build wheel (.whl)
- Verify metadata with twine

**Test Cases:**
1. ✅ Build with valid _version.py
2. ✅ Verify dist/ contents
3. ✅ Check metadata validity
4. ✅ Verify version in filenames

### 3. Release Script (`scripts/release.sh`)
**Purpose:** Publish package to PyPI or TestPyPI

**Key Functions:**
- Verify git working tree is clean
- Verify _version.py exists
- Verify git tag exists and matches HEAD
- Run build pipeline
- Upload to PyPI/TestPyPI

**Test Cases:**
1. ✅ Verify clean working tree check
2. ✅ Verify _version.py check
3. ✅ Verify git tag check
4. ✅ Test upload to TestPyPI (dry-run)

### 4. Makefile Targets
**Purpose:** Provide convenient commands for development and release

**Key Targets to Verify:**
- `make bump-version` - Version bumping
- `make build` - Package building
- `make publish-test` - TestPyPI publishing
- `make publish` - PyPI publishing
- `make info` - Environment info
- `make dev-setup` - Development setup
- `make quick-check` - Quick checks
- `make release-check` - Release preparation

## Verification Steps

### Phase 1: Environment Setup
1. ✅ Verify uv is installed
2. ✅ Verify Python environment
3. ✅ Install development dependencies
4. ✅ Verify all tools available

### Phase 2: Version Bumping Tests
1. ✅ Test bump_version.py with --set flag
2. ✅ Verify _version.py generation
3. ✅ Verify CHANGELOG.md updates
4. ✅ Test different bump types (patch/minor/major)
5. ✅ Verify version tuple generation

### Phase 3: Build Tests
1. ✅ Test build.sh script
2. ✅ Verify dist/ contents
3. ✅ Check wheel structure
4. ✅ Verify metadata
5. ✅ Test make build target

### Phase 4: Release Workflow Tests
1. ✅ Test release.sh validation checks
2. ✅ Verify git tag requirements
3. ✅ Test make publish-test (dry-run)
4. ✅ Document complete release workflow

### Phase 5: Integration Tests
1. ✅ Complete version bump → build → release workflow
2. ✅ Verify all make targets work
3. ✅ Test error handling
4. ✅ Document any issues found

## Expected Outcomes

### Version Bumping
- ✅ _version.py created with correct format
- ✅ CHANGELOG.md updated with new release section
- ✅ Unreleased section reset to template
- ✅ Comparison links updated
- ✅ Version tuple correctly generated

### Building
- ✅ dist/ directory contains .tar.gz and .whl
- ✅ Filenames include correct version
- ✅ Metadata passes twine check
- ✅ Wheel contains all necessary files

### Release
- ✅ All validation checks pass
- ✅ Git tag verified
- ✅ Working tree clean check works
- ✅ Upload process documented

## Issues to Watch For

### Potential Issues
1. ⚠️ Missing _version.py (hatch-vcs generates it)
2. ⚠️ CHANGELOG.md format issues
3. ⚠️ Git tag mismatches
4. ⚠️ Dirty working tree
5. ⚠️ Missing dependencies

### Solutions
1. ✅ Run bump_version.py to generate _version.py
2. ✅ Ensure CHANGELOG.md follows format
3. ✅ Create and verify git tags
4. ✅ Commit all changes before release
5. ✅ Install all dev dependencies

## Test Execution Plan

### Step 1: Initial State Check
```bash
# Check current state
make info
git status
ls -la src/spdx_headers/
```

### Step 2: Version Bump Test
```bash
# Test version bumping
python scripts/bump_version.py --set 1.0.2
cat src/spdx_headers/_version.py
cat CHANGELOG.md | head -30
```

### Step 3: Build Test
```bash
# Test building
make build
ls -la dist/
```

### Step 4: Metadata Verification
```bash
# Verify metadata
uv run --with twine python -m twine check dist/*
```

### Step 5: Release Validation Test
```bash
# Test release validation (without actual upload)
# This will fail on git tag check, which is expected
./scripts/release.sh --repository testpypi || echo "Expected to fail on tag check"
```

## Success Criteria

### Version Bumping ✅
- [ ] _version.py generated correctly
- [ ] CHANGELOG.md updated properly
- [ ] Version format correct (X.Y.Z)
- [ ] Links updated in CHANGELOG.md

### Building ✅
- [ ] Source distribution created
- [ ] Wheel created
- [ ] Metadata valid
- [ ] Correct version in filenames

### Release Process ✅
- [ ] All validation checks work
- [ ] Error messages clear
- [ ] Documentation complete
- [ ] Workflow documented

## Documentation Updates Needed

### If Issues Found
1. Document workarounds
2. Update scripts if needed
3. Add troubleshooting guide
4. Update README.md

### If All Works
1. ✅ Confirm all scripts functional
2. ✅ Document complete workflow
3. ✅ Add examples to README
4. ✅ Create release checklist

## Next Steps After Verification

1. Document complete release workflow
2. Create release checklist
3. Update README with release instructions
4. Test actual PyPI upload (if desired)
5. Create GitHub release automation (optional)