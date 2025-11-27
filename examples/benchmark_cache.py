#!/usr/bin/env python3
"""Benchmark script to demonstrate license data caching improvements."""

import time
from pathlib import Path

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from spdx_headers.data import (
    clear_license_data_cache,
    get_cache_info,
    load_license_data,
)


def benchmark_without_cache(iterations: int = 100) -> float:
    """Benchmark loading license data without cache (clearing each time)."""
    start = time.time()

    for _ in range(iterations):
        clear_license_data_cache()
        load_license_data()

    return time.time() - start


def benchmark_with_cache(iterations: int = 100) -> float:
    """Benchmark loading license data with cache."""
    # Clear cache first
    clear_license_data_cache()

    start = time.time()

    for _ in range(iterations):
        load_license_data()

    return time.time() - start


def main():
    """Run cache benchmarks."""
    print("=" * 70)
    print("License Data Caching Benchmark")
    print("=" * 70)

    # Warm up
    load_license_data()
    clear_license_data_cache()

    # Test with different iteration counts
    for iterations in [10, 50, 100, 200]:
        print(f"\n{'─' * 70}")
        print(f"Testing with {iterations} iterations:")
        print(f"{'─' * 70}")

        # Without cache (clearing each time)
        no_cache_time = benchmark_without_cache(iterations)

        # With cache
        with_cache_time = benchmark_with_cache(iterations)

        # Get cache info
        cache_info = get_cache_info()

        # Calculate improvement
        speedup = no_cache_time / with_cache_time if with_cache_time > 0 else 0
        improvement = (
            ((no_cache_time - with_cache_time) / no_cache_time * 100)
            if no_cache_time > 0
            else 0
        )

        print(f"  Without cache (cleared each time): {no_cache_time:.4f} seconds")
        print(f"  With cache (cached):                {with_cache_time:.4f} seconds")
        print(f"  Speedup:                            {speedup:.2f}x")
        print(f"  Improvement:                        {improvement:.1f}%")
        print(f"\n  Cache Statistics:")
        print(f"    Hits:     {cache_info['hits']}")
        print(f"    Misses:   {cache_info['misses']}")
        print(f"    Size:     {cache_info['currsize']}/{cache_info['maxsize']}")

        # Clear for next test
        clear_license_data_cache()

    print(f"\n{'=' * 70}")
    print("Benchmark complete!")
    print("=" * 70)
    print("\nKey benefits of caching:")
    print("  ✓ Eliminates repeated JSON parsing")
    print("  ✓ Instant access after first load")
    print("  ✓ Automatic cache management (LRU)")
    print("  ✓ Supports multiple data files")
    print("  ✓ Cache cleared on data updates")
    print("=" * 70)

    # Final demonstration
    print("\nFinal demonstration:")
    clear_license_data_cache()

    print("  First load (cache miss)...")
    start = time.time()
    load_license_data()
    first_load = time.time() - start
    print(f"    Time: {first_load:.4f} seconds")

    print("  Second load (cache hit)...")
    start = time.time()
    load_license_data()
    second_load = time.time() - start
    print(f"    Time: {second_load:.4f} seconds")

    speedup = first_load / second_load if second_load > 0 else 0
    print(f"  Cache speedup: {speedup:.0f}x faster!")

    cache_info = get_cache_info()
    print(f"\n  Final cache stats: {cache_info['hits']} hits, {cache_info['misses']} misses")


if __name__ == "__main__":
    main()