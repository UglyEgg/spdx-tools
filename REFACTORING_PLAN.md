# Code Quality Refactoring Plan

## Objective
Refactor long functions to improve readability and maintainability while keeping all tests passing.

## Functions to Refactor (Priority Order)

### High Priority (Will Refactor)

1. **`cli.py::main()` - 238 lines**
   - **Status:** SKIP - Acceptable for CLI entry point (mostly argparse setup)
   - **Rationale:** CLI main functions are typically long due to argument parsing

2. **`operations.py::add_header_to_py_files()` - 76 lines**
   - **Action:** Extract file processing logic into helper function
   - **Benefit:** Clearer separation of concerns

3. **`data.py::update_license_data()` - 67 lines**
   - **Action:** Extract HTTP request and file writing logic
   - **Benefit:** Easier to test and maintain

4. **`encoding.py::get_encoding_info()` - 63 lines**
   - **Action:** Extract chardet analysis into helper
   - **Benefit:** Clearer logic flow

5. **`operations.py::_wrap_license_text()` - 57 lines**
   - **Action:** Extract paragraph flushing logic (already has flush_paragraph)
   - **Benefit:** Reduce duplication

### Medium Priority (Consider)

6. **`core.py::save()` - 53 lines**
   - **Action:** Extract atomic write logic
   - **Benefit:** Reusable atomic write pattern

7. **`encoding.py::detect_encoding()` - 52 lines**
   - **Action:** Extract encoding attempt logic
   - **Benefit:** Clearer error handling

### Low Priority (Acceptable as-is)

- Functions 30-45 lines are generally acceptable
- Many have good structure already
- Refactoring may not provide significant benefit

## Refactoring Strategy

### Principles
1. **Extract helper functions** for complex logic blocks
2. **Maintain single responsibility** for each function
3. **Preserve all existing behavior** (no functional changes)
4. **Keep all tests passing** (241/241)
5. **Improve readability** without over-engineering

### Testing Strategy
- Run full test suite after each refactoring
- Verify no functional changes
- Ensure all 241 tests still pass

## Implementation Plan

### Phase 3A: operations.py Refactoring
- Extract file processing logic from `add_header_to_py_files()`
- Extract similar logic from `change_header_in_py_files()`
- Extract common error handling patterns

### Phase 3B: data.py Refactoring
- Extract HTTP request logic from `update_license_data()`
- Extract file writing logic
- Improve error messages

### Phase 3C: encoding.py Refactoring
- Extract chardet analysis from `get_encoding_info()`
- Simplify `detect_encoding()` logic flow

### Phase 3D: core.py Refactoring
- Extract atomic write pattern from `save()`
- Make it reusable across the codebase

## Success Criteria

- ✅ All 241 tests passing
- ✅ No functional changes
- ✅ Improved readability
- ✅ Reduced function length where beneficial
- ✅ Better separation of concerns
- ✅ Easier to test individual components

## Risk Assessment

**Risk Level:** 🟡 MEDIUM

**Mitigation:**
- Comprehensive test coverage (241 tests)
- Incremental changes
- Test after each refactoring
- Easy to rollback if needed