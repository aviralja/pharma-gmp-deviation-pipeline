"""
Performance Testing Script for GMP APIs

This script helps you benchmark the original vs optimized implementations
to measure actual performance improvements.
"""

import time
import json
from src.brainstorming import brain as brain_original
from src.brainstorming_optimized import brain_with_timing, brain_optimized
from src.gmp_dev_generator import deviation_generation as gmp_original
from src.gmp_dev_generator_optimized import deviation_generation_with_timing, deviation_generation_optimized


def test_brainstorming(test_data):
    """Test both brainstorming implementations"""
    
    print("\n" + "="*80)
    print("TESTING BRAINSTORMING API")
    print("="*80)
    
    # Test original with timing
    print("\n📊 ORIGINAL IMPLEMENTATION (WITH TIMING):")
    print("-" * 80)
    start = time.time()
    result_original = brain_with_timing(test_data)
    original_time = time.time() - start
    
    # Test optimized
    print("\n🚀 OPTIMIZED IMPLEMENTATION:")
    print("-" * 80)
    start = time.time()
    result_optimized = brain_optimized(test_data)
    optimized_time = time.time() - start
    
    # Summary
    print("\n" + "="*80)
    print("BRAINSTORMING PERFORMANCE SUMMARY")
    print("="*80)
    print(f"Original Time:   {original_time:.2f}s")
    print(f"Optimized Time:  {optimized_time:.2f}s")
    print(f"Improvement:     {original_time - optimized_time:.2f}s ({((original_time - optimized_time) / original_time * 100):.1f}% faster)")
    print("="*80)
    
    return result_original, result_optimized, original_time, optimized_time


def test_gmp_generation(test_data):
    """Test both GMP generation implementations"""
    
    print("\n" + "="*80)
    print("TESTING GMP GENERATION API")
    print("="*80)
    
    # Test original with timing
    print("\n📊 ORIGINAL IMPLEMENTATION (WITH TIMING):")
    print("-" * 80)
    start = time.time()
    result_original = deviation_generation_with_timing(test_data)
    original_time = time.time() - start
    
    # Test optimized
    print("\n🚀 OPTIMIZED IMPLEMENTATION:")
    print("-" * 80)
    start = time.time()
    result_optimized = deviation_generation_optimized(test_data)
    optimized_time = time.time() - start
    
    # Summary
    print("\n" + "="*80)
    print("GMP GENERATION PERFORMANCE SUMMARY")
    print("="*80)
    print(f"Original Time:   {original_time:.2f}s")
    print(f"Optimized Time:  {optimized_time:.2f}s")
    print(f"Improvement:     {original_time - optimized_time:.2f}s ({((original_time - optimized_time) / original_time * 100):.1f}% faster)")
    print("="*80)
    
    return result_original, result_optimized, original_time, optimized_time


if __name__ == "__main__":
    print("\n" + "🔬 PERFORMANCE BENCHMARK TOOL" + "\n")
    
    # Sample test data for brainstorming
    brainstorming_test_data = {
        "Problem Description and Immediate Action": """
        During routine quality inspection of Batch #12345 of Product XYZ, 
        it was discovered that the temperature monitoring system failed to record 
        data for a 2-hour period during the critical sterilization phase. 
        The batch was immediately quarantined and investigation initiated.
        """
    }
    
    # Sample test data for GMP generation
    gmp_test_data = {
        "Problem Description": "Temperature excursion during storage",
        "Root Cause": "Equipment malfunction due to improper maintenance",
        "Corrective Actions": "Equipment repaired and preventive maintenance schedule updated",
        "Impact Assessment": "No impact on product quality confirmed through stability testing"
    }
    
    print("Choose test to run:")
    print("1. Brainstorming API")
    print("2. GMP Generation API")
    print("3. Both")
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        test_brainstorming(brainstorming_test_data)
    
    if choice in ["2", "3"]:
        test_gmp_generation(gmp_test_data)
    
    print("\n✅ Benchmark completed!\n")
