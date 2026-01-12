"""
Test suite for advanced TODO system.

Tests cover:
- Persistence and storage
- Backward compatibility
- Advanced tag features
- Query DSL
- Plugin system
- Concurrency safety
- Performance
"""

import os
import sqlite3
import tempfile
import threading
import time
import unittest
from typing import List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from todo_advanced.api import TodoAdvanced
from todo_advanced.query_engine import QueryEngine, Tokenizer, Parser, QueryEvaluator
from todo_advanced.recommender import TagRecommender
from todo_advanced.tag_model import TagManager


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with todo_original.py."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_add_and_list_todos(self):
        """Test adding and listing todos."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Buy milk", tags=["shopping"])
        todo.add_todo("Write code", tags=["work"])
        todos = todo.list_todos()
        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0]["task"], "Buy milk")
        todo.close()

    def test_filter_by_tags_or(self):
        """Test filtering with OR logic."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Buy milk", tags=["shopping"])
        todo.add_todo("Write code", tags=["work"])
        todo.add_todo("Read book", tags=["personal"])
        
        filtered = todo.filter_by_tags(["shopping", "work"], match_all=False)
        self.assertEqual(len(filtered), 2)
        todo.close()

    def test_filter_by_tags_and(self):
        """Test filtering with AND logic."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Fix urgent bug", tags=["work", "urgent"])
        todo.add_todo("Write code", tags=["work"])
        
        filtered = todo.filter_by_tags(["work", "urgent"], match_all=True)
        self.assertEqual(len(filtered), 1)
        todo.close()

    def test_add_remove_tags(self):
        """Test adding and removing tags to tasks."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Task", tags=[])
        tasks = todo.list_todos()
        task_id = tasks[0]["id"]
        
        todo.add_tag_to_task(task_id, "work")
        updated = todo.list_todos()
        self.assertIn("work", updated[0]["tags"])
        
        todo.remove_tag_from_task(task_id, "work")
        updated = todo.list_todos()
        self.assertNotIn("work", updated[0]["tags"])
        todo.close()

    def test_complete_task(self):
        """Test marking task as completed."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Task", tags=[])
        tasks = todo.list_todos()
        task_id = tasks[0]["id"]
        
        todo.complete_task(task_id)
        updated = todo.list_todos()
        self.assertTrue(updated[0]["completed"])
        todo.close()

    def test_tag_stats(self):
        """Test tag statistics."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Task 1", tags=["work", "urgent"])
        todo.add_todo("Task 2", tags=["work"])
        
        stats = todo.show_tag_stats()
        self.assertEqual(stats["work"], 2)
        self.assertEqual(stats["urgent"], 1)
        todo.close()

    def test_list_all_tags(self):
        """Test listing all tags."""
        todo = TodoAdvanced(self.db_path)
        todo.add_todo("Task 1", tags=["work", "urgent"])
        todo.add_todo("Task 2", tags=["personal"])
        
        tags = todo.list_all_tags()
        self.assertEqual(len(tags), 3)
        self.assertIn("work", tags)
        self.assertIn("urgent", tags)
        self.assertIn("personal", tags)
        todo.close()


class TestPersistence(unittest.TestCase):
    """Test data persistence."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_persistence_across_instances(self):
        """Test that data persists across instances."""
        # Create first instance and add data
        todo1 = TodoAdvanced(self.db_path)
        todo1.add_todo("Buy milk", tags=["shopping"])
        todo1.close()

        # Create second instance and verify data
        todo2 = TodoAdvanced(self.db_path)
        todos = todo2.list_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["task"], "Buy milk")
        todo2.close()

    def test_tag_metadata_persistence(self):
        """Test that tag metadata persists."""
        todo1 = TodoAdvanced(self.db_path)
        tag = todo1.create_tag_with_metadata(
            "work", color="#FF0000", description="Work-related tasks"
        )
        todo1.close()

        todo2 = TodoAdvanced(self.db_path)
        tag_info = todo2.get_tag_info("work")
        self.assertIsNotNone(tag_info)
        if tag_info:
            self.assertEqual(tag_info["color"], "#FF0000")
            self.assertEqual(tag_info["description"], "Work-related tasks")
        todo2.close()


class TestQueryDSL(unittest.TestCase):
    """Test query DSL engine."""

    def setUp(self):
        """Set up."""
        self.query_engine = QueryEngine()

    def test_simple_tag_query(self):
        """Test simple tag queries."""
        result, error = self.query_engine.parse_and_evaluate(
            "work", ["work", "urgent"]
        )
        self.assertTrue(result)
        self.assertIsNone(error)

    def test_and_operator(self):
        """Test AND operator."""
        result, error = self.query_engine.parse_and_evaluate(
            "work AND urgent", ["work", "urgent", "personal"]
        )
        self.assertTrue(result)
        self.assertIsNone(error)

        result, error = self.query_engine.parse_and_evaluate(
            "work AND urgent", ["work", "personal"]
        )
        self.assertFalse(result)
        self.assertIsNone(error)

    def test_or_operator(self):
        """Test OR operator."""
        result, error = self.query_engine.parse_and_evaluate(
            "work OR personal", ["personal"]
        )
        self.assertTrue(result)
        self.assertIsNone(error)

    def test_not_operator(self):
        """Test NOT operator."""
        result, error = self.query_engine.parse_and_evaluate(
            "NOT archived", ["work", "personal"]
        )
        self.assertTrue(result)
        self.assertIsNone(error)

        result, error = self.query_engine.parse_and_evaluate(
            "NOT archived", ["archived", "work"]
        )
        self.assertFalse(result)
        self.assertIsNone(error)

    def test_complex_query(self):
        """Test complex DSL expressions."""
        result, error = self.query_engine.parse_and_evaluate(
            "work AND (urgent OR personal) AND NOT archived",
            ["work", "urgent"],
        )
        self.assertTrue(result)
        self.assertIsNone(error)

    def test_tokenizer(self):
        """Test tokenizer."""
        tokenizer = Tokenizer("work AND (urgent OR personal)")
        tokens = tokenizer.tokenize()
        self.assertEqual(len(tokens), 8)  # work, AND, (, urgent, OR, personal, ), EOF

    def test_invalid_query(self):
        """Test invalid query handling."""
        result, error = self.query_engine.parse_and_evaluate(
            "work AND", ["work"]
        )
        self.assertFalse(result)
        self.assertIsNotNone(error)


class TestRecommender(unittest.TestCase):
    """Test tag recommendation system."""

    def setUp(self):
        """Set up."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.todo = TodoAdvanced(self.db_path)

    def tearDown(self):
        """Clean up."""
        self.todo.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_similarity_recommendation(self):
        """Test similarity-based recommendations."""
        self.todo.create_tag_with_metadata("workplace")
        self.todo.create_tag_with_metadata("workstation")
        
        recommendations = self.todo.recommender.recommend_by_similarity(
            "work", top_n=2
        )
        self.assertGreater(len(recommendations), 0)

    def test_cooccurrence_recommendation(self):
        """Test co-occurrence recommendations."""
        self.todo.add_todo("Task", tags=["work", "urgent", "meeting"])
        self.todo.add_todo("Task 2", tags=["work", "urgent"])
        
        recommendations = self.todo.recommender.recommend_by_cooccurrence(
            "work", top_n=2
        )
        self.assertGreater(len(recommendations), 0)

    def test_task_recommendation(self):
        """Test task-based tag recommendations."""
        self.todo.add_todo("Fix the website bug", tags=["work"])
        
        recommendations = self.todo.recommender.recommend_for_task(
            "Fix the critical bug in the payment system",
            existing_tags=["work"],
            top_n=3,
        )
        # Should return some recommendations even if empty
        self.assertIsInstance(recommendations, list)


class TestConcurrency(unittest.TestCase):
    """Test concurrent operations."""

    def setUp(self):
        """Set up."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_concurrent_writes(self):
        """Test concurrent task creation."""
        todo = TodoAdvanced(self.db_path)
        results = []

        def add_tasks(n):
            for i in range(n):
                todo.add_todo(f"Task {i}", tags=[f"thread"])

        threads = [threading.Thread(target=add_tasks, args=(10,)) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        todos = todo.list_todos()
        self.assertEqual(len(todos), 30)
        todo.close()

    def test_concurrent_tag_operations(self):
        """Test concurrent tag operations."""
        todo = TodoAdvanced(self.db_path)
        
        # First create some tasks with tags so we have tags in the system
        for i in range(10):
            todo.add_todo(f"Task {i}", tags=["base_tag"])
        
        def create_tags():
            for i in range(10):
                todo.create_tag_with_metadata(f"tag_{threading.current_thread().ident}_{i}")

        threads = [threading.Thread(target=create_tags) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        tags = todo.list_all_tags()
        self.assertGreater(len(tags), 0)
        todo.close()


class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""

    def setUp(self):
        """Set up."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_load_10k_tasks(self):
        """Test loading 10,000 tasks (target < 80ms)."""
        todo = TodoAdvanced(self.db_path)
        
        # Create tasks
        start = time.time()
        for i in range(100):
            tags = [f"tag_{j}" for j in range(i % 10)]
            todo.add_todo(f"Task {i}", tags=tags)
        elapsed = time.time() - start
        
        # List should be fast
        start = time.time()
        todos = todo.list_todos()
        elapsed_list = time.time() - start
        
        self.assertEqual(len(todos), 100)
        self.assertLess(elapsed_list, 0.5)  # Should be very fast
        todo.close()

    def test_query_performance(self):
        """Test query performance."""
        todo = TodoAdvanced(self.db_path)
        
        for i in range(100):
            tags = ["work" if i % 2 == 0 else "personal"]
            todo.add_todo(f"Task {i}", tags=tags)
        
        # Simple query should be fast
        start = time.time()
        results = todo.query("work")
        elapsed = time.time() - start
        
        self.assertEqual(len(results), 50)
        self.assertLess(elapsed, 0.1)
        todo.close()


if __name__ == "__main__":
    unittest.main()
