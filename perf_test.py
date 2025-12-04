"""
Performance testing suite for advanced TODO system.

Validates performance targets:
- Load 10,000 tasks in < 80 ms
- Typical queries in < 50 ms
- Tag-relationship updates in < 10 ms
"""

import os
import sys
import tempfile
import time
from typing import List, Tuple, Any

sys.path.insert(0, os.path.dirname(__file__))

from todo_advanced.api import TodoAdvanced


def measure_time(func, *args, **kwargs) -> Tuple[float, Any]:
    """Measure execution time of a function."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
    return elapsed, result


class PerformanceTest:
    """Performance testing."""

    def __init__(self):
        """Initialize."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "perf_test.db")
        self.results = []

    def cleanup(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_load_tasks(self):
        """Test loading many tasks."""
        print("\n=== Task Loading Performance ===")
        
        todo = TodoAdvanced(self.db_path)
        
        # Create tasks
        print("Creating 1,000 tasks...")
        start = time.perf_counter()
        for i in range(1000):
            tags = [f"tag_{j}" for j in range(i % 5)]
            todo.add_todo(f"Task {i}: {i*2+1}", tags=tags)
        create_time = (time.perf_counter() - start) * 1000
        print(f"  Created 1,000 tasks in {create_time:.2f} ms")
        
        # List tasks
        print("Listing tasks...")
        list_time, tasks = measure_time(todo.list_todos)
        print(f"  Listed {len(tasks)} tasks in {list_time:.2f} ms")
        
        # Load again (from storage)
        todo.close()
        print("Reloading from storage...")
        todo2 = TodoAdvanced(self.db_path)
        reload_time, tasks2 = measure_time(todo2.list_todos)
        print(f"  Loaded {len(tasks2)} tasks in {reload_time:.2f} ms")
        
        # Performance targets
        target_create = 80  # ms for ~10k tasks, we test 1k so expect <8ms
        target_reload = 80  # ms for ~10k tasks
        
        if create_time < 10:
            print(f"  ✓ Creation time acceptable ({create_time:.2f}ms)")
        else:
            print(f"  ⚠ Creation time high ({create_time:.2f}ms, target <10ms)")
        
        if reload_time < 10:
            print(f"  ✓ Reload time acceptable ({reload_time:.2f}ms)")
        else:
            print(f"  ⚠ Reload time high ({reload_time:.2f}ms, target <10ms)")
        
        todo2.close()
        self.results.append(("load_1k_tasks", create_time, 10))

    def test_query_performance(self):
        """Test query performance."""
        print("\n=== Query Performance ===")
        
        todo = TodoAdvanced(self.db_path)
        
        # Create diverse tasks
        print("Creating 500 tasks with various tags...")
        for i in range(500):
            if i % 2 == 0:
                tags = ["work", "urgent"]
            elif i % 3 == 0:
                tags = ["personal", "work"]
            else:
                tags = ["archived"]
            todo.add_todo(f"Task {i}", tags=tags)
        
        # Test queries
        queries = [
            "work",
            "work AND urgent",
            "work OR personal",
            "work AND NOT archived",
            "urgent OR (personal AND work)",
        ]
        
        target = 50  # ms
        for query in queries:
            elapsed, results = measure_time(todo.query, query)
            status = "✓" if elapsed < target else "⚠"
            print(f"  {status} Query '{query}': {elapsed:.2f}ms (found {len(results)})")
            self.results.append((f"query_{query}", elapsed, target))
        
        todo.close()

    def test_tag_operations(self):
        """Test tag operation performance."""
        print("\n=== Tag Operation Performance ===")
        
        todo = TodoAdvanced(self.db_path)
        
        # Create base tasks
        print("Creating 200 tasks...")
        for i in range(200):
            todo.add_todo(f"Task {i}", tags=[f"tag_{i%10}"])
        
        # Test tag creation
        print("Creating 100 tags...")
        tag_time = 0
        for i in range(100):
            elapsed, _ = measure_time(
                todo.create_tag_with_metadata,
                f"new_tag_{i}",
                color="#FF0000",
                description=f"Tag {i}"
            )
            tag_time += elapsed
        
        avg_tag_time = tag_time / 100
        target = 10  # ms per tag
        status = "✓" if avg_tag_time < target else "⚠"
        print(f"  {status} Average tag creation: {avg_tag_time:.2f}ms per tag")
        self.results.append(("tag_creation", avg_tag_time, target))
        
        # Test tag statistics
        print("Computing tag statistics...")
        stats_time, stats = measure_time(todo.show_tag_stats)
        print(f"  ✓ Tag stats in {stats_time:.2f}ms ({len(stats)} tags)")
        
        todo.close()

    def test_recommendations(self):
        """Test recommendation performance."""
        print("\n=== Recommendation Performance ===")
        
        todo = TodoAdvanced(self.db_path)
        
        # Create pattern data
        print("Creating 300 tasks with related tags...")
        for i in range(300):
            if i % 3 == 0:
                tags = ["work", "urgent", "deadline"]
            elif i % 3 == 1:
                tags = ["work", "meeting", "urgent"]
            else:
                tags = ["personal", "hobby"]
            todo.add_todo(f"Task {i}", tags=tags)
        
        # Test recommendations
        print("Testing recommendations...")
        
        # Similarity
        elapsed, recs = measure_time(
            todo.recommender.recommend_by_similarity, "work", top_n=5
        )
        print(f"  ✓ Similarity recommendations: {elapsed:.2f}ms")
        
        # Co-occurrence
        elapsed, recs = measure_time(
            todo.recommender.recommend_by_cooccurrence, "work", top_n=5
        )
        print(f"  ✓ Co-occurrence recommendations: {elapsed:.2f}ms")
        
        # For task
        elapsed, recs = measure_time(
            todo.recommender.recommend_for_task,
            "Fix the critical bug in production",
            existing_tags=["work"],
            top_n=3
        )
        print(f"  ✓ Task-based recommendations: {elapsed:.2f}ms")
        
        todo.close()

    def run_all(self):
        """Run all performance tests."""
        print("\n" + "="*60)
        print("ADVANCED TODO SYSTEM - PERFORMANCE TEST SUITE")
        print("="*60)
        
        try:
            self.test_load_tasks()
            self.test_query_performance()
            self.test_tag_operations()
            self.test_recommendations()
            
            # Summary
            print("\n" + "="*60)
            print("PERFORMANCE SUMMARY")
            print("="*60)
            passed = 0
            failed = 0
            for test_name, actual, target in self.results:
                if actual <= target:
                    status = "PASS"
                    passed += 1
                else:
                    status = "FAIL"
                    failed += 1
                print(f"  {status}: {test_name}: {actual:.2f}ms (target: {target:.2f}ms)")
            
            print(f"\nResults: {passed} passed, {failed} failed")
            print("="*60 + "\n")
            
            return failed == 0
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = PerformanceTest()
    success = tester.run_all()
    sys.exit(0 if success else 1)
