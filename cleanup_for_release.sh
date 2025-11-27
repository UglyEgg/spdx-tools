#!/bin/bash
# cleanup_for_release.sh - Remove development cruft before PyPI release

echo "🧹 Cleaning up repository for PyPI release..."

# Remove internal development docs
echo "Removing internal development documentation..."
rm -f CONSOLIDATION_SUMMARY.md
rm -f COVERAGE_100_PLAN.md
rm -f CURRENT_STATUS_AND_NEXT_STEPS.md
rm -f ENCODING_ERRORS_SUMMARY.md
rm -f ENTERPRISE_QUALITY_REVIEW.md
rm -f FILE_IO_OPTIMIZATION_SUMMARY.md
rm -f FINAL_COMPREHENSIVE_SUMMARY.md
rm -f FINAL_TEST_SUMMARY.md
rm -f GITHUB_ACTIONS_FIX.md
rm -f LICENSE_CACHING_SUMMARY.md
rm -f MANUAL_COMPLETION_GUIDE.md
rm -f PR6_COMPLETE_SUMMARY.md
rm -f PR7_CONFLICT_RESOLUTION.md
rm -f REFACTORING_PLAN.md
rm -f TEST_COVERAGE_SUMMARY.md
rm -f VERIFICATION_PLAN.md
rm -f encoding_test_fixes.patch
rm -f pr_body.md
rm -f pr_body_100_coverage.md
rm -f pr_body_encoding.md
rm -f pr_body_tests.md
rm -f todo.md

# Move benchmarks to examples
echo "Moving benchmark scripts to examples/..."
mkdir -p examples
mv benchmark_cache.py examples/ 2>/dev/null || rm -f benchmark_cache.py
mv benchmark_io.py examples/ 2>/dev/null || rm -f benchmark_io.py

echo "✅ Cleanup complete!"
echo ""
echo "Files removed: 22 internal development documents"
echo "Files moved: 2 benchmark scripts → examples/"
echo ""
echo "Next steps:"
echo "1. Fix dependencies in pyproject.toml"
echo "2. Run: make test"
echo "3. Run: make lint"
echo "4. Run: make build"
echo "5. Publish to PyPI"