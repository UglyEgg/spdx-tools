#!/usr/bin/env python3
"""Benchmark script to demonstrate file I/O optimization improvements."""

import tempfile
import time
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from spdx_headers.core import FileProcessor, create_header
from spdx_headers.data import load_license_data


def create_test_files(directory: Path, count: int = 100) -> list[Path]:
    """Create test Python files."""
    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(count):
        filepath = directory / f"test_file_{i}.py"
        filepath.write_text(f"""#!/usr/bin/env python3
# Test file {i}

def function_{i}():
    '''Test function {i}'''
    return {i}

if __name__ == '__main__':
    print(function_{i}())
""")
        files.append(filepath)
    return files


def benchmark_old_approach(files: list[Path], header: str) -> float:
    """Benchmark the old multi-pass approach with realistic workflow."""
    start = time.time()
    
    for filepath in files:
        # Read 1: has_spdx_header() check
        with open(filepath, 'r') as f:
            content = f.read(2048)
            has_header = 'SPDX' in content
        
        if not has_header:
            # Read 2: extract_spdx_header() to check structure
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Read 3: remove_spdx_header() to get clean content
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Process
            shebang = ""
            if lines and lines[0].startswith("#!"):
                shebang = lines.pop(0)
            
            new_lines = []
            if shebang:
                new_lines.append(shebang)
            new_lines.extend(header.splitlines(keepends=True))
            new_lines.extend(lines)
            
            # Write (non-atomic)
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
    
    return time.time() - start


def benchmark_new_approach(files: list[Path], header: str) -> float:
    """Benchmark the new single-pass approach."""
    start = time.time()
    
    for filepath in files:
        # Single-pass processing with atomic write
        processor = FileProcessor(filepath)
        processor.load()  # Read once
        
        if not processor.has_header():  # Check in memory
            processor.add_header(header)  # Modify in memory
            processor.save()  # Write once (atomic)
    
    return time.time() - start


def main():
    """Run benchmarks."""
    print("=" * 70)
    print("File I/O Optimization Benchmark")
    print("=" * 70)
    
    # Load license data
    license_data = load_license_data()
    header = create_header(
        license_data,
        "MIT",
        "2024",
        "Test User",
        "test@example.com"
    )
    
    if not header:
        print("Error: Could not create header")
        return
    
    # Test with different file counts
    for file_count in [10, 50, 100, 200]:
        print(f"\n{'─' * 70}")
        print(f"Testing with {file_count} files:")
        print(f"{'─' * 70}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Old approach
            files = create_test_files(tmppath / "old", file_count)
            old_time = benchmark_old_approach(files, header)
            
            # New approach
            files = create_test_files(tmppath / "new", file_count)
            new_time = benchmark_new_approach(files, header)
            
            # Calculate improvement
            speedup = old_time / new_time if new_time > 0 else 0
            improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0
            
            print(f"  Old approach (multi-pass):  {old_time:.4f} seconds")
            print(f"  New approach (single-pass): {new_time:.4f} seconds")
            print(f"  Speedup:                    {speedup:.2f}x")
            print(f"  Improvement:                {improvement:.1f}%")
    
    print(f"\n{'=' * 70}")
    print("Benchmark complete!")
    print("=" * 70)
    print("\nKey improvements:")
    print("  ✓ Single file read instead of multiple reads")
    print("  ✓ Atomic writes prevent file corruption")
    print("  ✓ Better memory efficiency")
    print("  ✓ Cleaner, more maintainable code")
    print("=" * 70)


if __name__ == "__main__":
    main()