## Summary

This PR adds comprehensive encoding detection and improved error handling with custom exception classes and helpful error messages.

## New Features

### 1. Encoding Detection
- Auto-detect file encoding (UTF-8, Latin-1, Windows-1252, ASCII)
- Optional chardet support for better detection
- Preserve original file encoding
- Handle UTF-8 BOM
- Detect binary files

### 2. Custom Exception Classes
- SPDXError (base exception)
- FileProcessingError
- EncodingError
- LicenseNotFoundError (with fuzzy matching)
- DirectoryNotFoundError
- NoFilesFoundError
- HeaderNotFoundError
- InvalidHeaderError
- ConcurrentModificationError
- PermissionError

### 3. Improved Error Messages
- Helpful suggestions for fixing issues
- Fuzzy matching for license names
- Clear context and actionable guidance
- Professional error formatting

## Error Message Examples

### Before
```
Error: License keyword 'apache' is not supported.
```

### After
```
License 'apache' not found in the SPDX license database.

Did you mean one of these?
  • Apache-2.0
  • Apache-1.1
  • Apache-1.0

Use 'spdx-headers --list apache' to search for licenses.
```

## New Modules

### exceptions.py (~250 lines)
- Custom exception classes
- Fuzzy matching helper
- Helpful error messages with suggestions

### encoding.py (~290 lines)
- detect_encoding() - Auto-detect file encoding
- read_file_with_encoding() - Read with auto-detection
- write_file_with_encoding() - Write with encoding
- is_text_file() - Check if file is text
- get_encoding_info() - Get detailed encoding info

## Benefits

- Better user experience with clear error messages
- Automatic encoding handling for international files
- Fuzzy matching suggests correct license names
- Graceful error handling and recovery
- Professional error messages with suggestions

## Testing

All 24 tests pass. All code quality checks pass.

## Backward Compatibility

No breaking changes. Existing code continues to work. New features are optional and automatic.

## Optional Dependencies

- chardet: Optional for better encoding detection
- Falls back gracefully if not installed

## Documentation

See ENCODING_ERRORS_SUMMARY.md for comprehensive documentation, usage examples, and technical details.

## Related PRs

- PR #2: Code consolidation (merged)
- PR #3: File I/O optimization (pending)
- PR #4: License caching (pending)