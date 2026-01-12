# Advanced Tag System - Feature Specification

## Executive Summary

This document details the complete specification for the Advanced Tag System enhancement to the minimal TODO application. The system provides persistent storage, structured tag management, advanced querying, and a plugin architecture while maintaining 100% backward compatibility with the existing API.

## 1. Requirements Overview

### 1.1 Persistence Requirements

**Requirement**: All tasks, tags, and metadata must survive application restarts and concurrent accesses.

**Implementation**:
- SQLite database as primary storage backend
- Automatic database initialization and schema migration
- Atomic transactions for critical operations
- Thread-safe read/write operations with lock protection
- Support for schema evolution

**Validation**:
- Data persists across instance restarts
- No data corruption under concurrent writes (30+ threads)
- Schema versioning for future migrations

### 1.2 Structured Tag Model

**Requirement**: Tags must be more than strings - they need metadata, relationships, and usage tracking.

**Tag Properties**:
- `name`: Unique identifier
- `color`: CSS color for CLI display (default: #808080)
- `description`: Human-readable description
- `aliases`: Alternative names (e.g., "work" ↔ "office")
- `usage_count`: Number of times tag has been used
- `created_at`: ISO timestamp
- `updated_at`: ISO timestamp
- `cooccurrence`: Dictionary of {tag_name: count} for relationship tracking

**Implementation**:
- `Tag` class with metadata management
- `TagManager` for CRUD operations and relationships
- Alias resolution and canonicalization
- Automatic usage tracking on each use
- Co-occurrence graph built from task assignments

### 1.3 Query DSL Requirements

**Requirement**: Support complex tag queries with boolean operators and parentheses.

**Query Syntax**:
```
tag:work AND (urgent OR personal) AND NOT archived
```

**Supported Operators**:
- `AND`: All conditions must match
- `OR`: At least one condition must match
- `NOT`: Condition must not match
- Parentheses for precedence

**Implementation**:
- Tokenizer: Break expression into tokens
- Parser: Build Abstract Syntax Tree (AST)
- Evaluator: Traverse AST against task tags
- Error handling with descriptive messages
- Performance: Simple queries < 50ms on 1000 tasks

### 1.4 Tag Recommendation System

**Requirement**: Automatically suggest relevant tags based on task content and history.

**Recommendation Methods**:
1. **Keyword Similarity**: Match keywords in task text to tag names
   - Exact match: 1.0
   - Substring match: 0.8
   - Character overlap: proportional
   - Threshold: > 0.3

2. **Co-occurrence**: Suggest tags that frequently appear together
   - Based on historical task assignments
   - Weighted by frequency
   - Top N results returned

3. **Task Context**: Combine keyword and co-occurrence scoring
   - Keyword similarity weight: 0.7
   - Co-occurrence weight: 0.3
   - Return top N recommendations

**Implementation**:
- `TagRecommender` class
- Caching of recommendation results
- Fast similarity calculations
- Performance: < 20ms for recommendations

### 1.5 Concurrency Safety

**Requirement**: System must safely handle concurrent operations without data corruption.

**Safety Measures**:
- RLock (reentrant mutex) for all database operations
- Atomic transactions for multi-step operations
- No dirty reads or lost updates
- Support for 30+ concurrent threads

**Test Coverage**:
- Concurrent task creation (30 threads, 10 tasks each)
- Concurrent tag operations
- Concurrent query execution
- Stress tests with 1000+ concurrent operations

### 1.6 Backward Compatibility

**Requirement**: All existing `todo_original.py` code must work unchanged.

**API Preservation**:
```python
# All these must work identically to todo_original.py
add_todo(task, tags=None)
list_todos()
filter_by_tags(tags, match_all=False)
add_tag_to_task(index, tag)
remove_tag_from_task(index, tag)
complete_task(index)
show_tag_stats()
list_all_tags()
```

**Implementation**:
- Module-level functions that delegate to `TodoAdvanced` instance
- Index-based API for backward compatibility
- Same return types and error handling
- No breaking changes

## 2. Architecture

### 2.1 Module Structure

```
todo_advanced/
├── __init__.py           # Package initialization, exports
├── api.py               # Public API, backward compatibility layer
├── storage.py           # SQLite storage backend
├── tag_model.py         # Tag class and TagManager
├── query_engine.py      # DSL tokenizer, parser, evaluator
├── recommender.py       # Tag recommendation engine
└── plugin_manager.py    # Plugin system with hooks
```

### 2.2 Data Model

#### Tasks Table
```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    tags TEXT,                    -- JSON array
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

#### Tags Table
```sql
CREATE TABLE tags (
    name TEXT PRIMARY KEY,
    color TEXT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    aliases TEXT                  -- JSON array
)
```

#### Co-occurrence Table
```sql
CREATE TABLE cooccurrence (
    tag1 TEXT,
    tag2 TEXT,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (tag1, tag2),
    FOREIGN KEY (tag1) REFERENCES tags(name),
    FOREIGN KEY (tag2) REFERENCES tags(name)
)
```

### 2.3 Component Details

#### Storage Backend

**Interface**:
```python
class StorageBackend(ABC):
    def save_task(self, task_id: str, task_data: Dict) -> None
    def load_task(self, task_id: str) -> Optional[Dict]
    def delete_task(self, task_id: str) -> None
    def list_tasks(self) -> List[Dict]
    def save_tag(self, tag_name: str, tag_data: Dict) -> None
    def load_tag(self, tag_name: str) -> Optional[Dict]
    def delete_tag(self, tag_name: str) -> None
    def list_tags(self) -> List[str]
    def save_cooccurrence(self, tag1: str, tag2: str, count: int) -> None
    def load_cooccurrence(self, tag1: str, tag2: str) -> int
    def close(self) -> None
```

**Implementation**: `SQLiteStorage`
- Thread-safe with RLock
- Automatic connection management
- JSON serialization for complex types
- Index optimization for common queries

#### Tag Manager

**Operations**:
- Create tags with metadata
- Get tags by name or alias
- Resolve aliases to canonical names
- Record usage and co-occurrence
- Update tag metadata
- Delete tags

#### Query Engine

**Components**:
1. **Tokenizer**: Convert string to tokens
   - Recognizes: TAG, AND, OR, NOT, LPAREN, RPAREN
   - Handles whitespace and delimiters

2. **Parser**: Build AST from tokens
   - Handles operator precedence
   - Supports parentheses
   - Generates error messages

3. **Evaluator**: Evaluate AST against tags
   - Recursive evaluation
   - Short-circuit evaluation for AND/OR
   - Boolean logic for NOT

#### Recommender

**Scoring System**:
- Keyword similarity: 0-1.0 based on string matching
- Co-occurrence: Raw count, normalized by frequency
- Combined score: 0.7 * keyword_score + 0.3 * cooccurrence_score

#### Plugin Manager

**Features**:
- Auto-discovery from plugin directory
- Hook registration and triggering
- Safe exception handling
- Available hooks:
  - `on_task_added(task_id, task, tags)`
  - `on_task_removed(task_id)`
  - `on_task_completed(task_id)`
  - `on_tag_added(tag_name, metadata)`
  - `on_tag_removed(tag_name)`
  - `on_query(expression, results)`

## 3. API Specifications

### 3.1 Core API (Backward Compatible)

#### add_todo(task: str, tags: Optional[List[str]] = None) -> None
Add a task with optional tags.
- Creates task with unique UUID
- Initializes/updates tags in tag manager
- Records co-occurrence relationships
- Triggers `on_task_added` hook

#### list_todos() -> List[Dict]
Return all tasks in current form.
- Returns list of task dictionaries
- Each dict has: id, task, completed, tags
- Ordered by creation time (newest first)

#### filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]
Filter tasks by tags.
- `match_all=False` (default): OR logic - at least one tag must match
- `match_all=True`: AND logic - all tags must match
- Empty tag list returns all tasks

#### add_tag_to_task(index: int, tag: str) -> None
Add a tag to a task by index.
- Ensures tag exists in tag manager
- Records usage
- Raises IndexError if index out of range

#### remove_tag_from_task(index: int, tag: str) -> None
Remove a tag from a task.
- Does nothing if tag not present
- Raises IndexError if index out of range

#### complete_task(index: int) -> None
Mark a task as completed.
- Sets completed flag to True
- Triggers `on_task_completed` hook
- Raises IndexError if index out of range

#### show_tag_stats() -> Dict[str, int]
Return tag usage statistics.
- Returns dict of {tag_name: usage_count}
- Counts only tasks with that tag

#### list_all_tags() -> List[str]
Return all distinct tags.
- Returns sorted list of tag names
- Includes aliases as separate entries

### 3.2 Advanced API

#### TodoAdvanced Class

**Constructor**:
```python
TodoAdvanced(db_path: str = "todo_advanced.db", 
             plugin_dir: Optional[str] = None)
```

**Methods**:
- All backward-compatible methods plus:
- `query(expression: str) -> List[Dict]`: Execute DSL query
- `recommend_tags_for_task(task, tags, top_n) -> List[Tuple]`: Get recommendations
- `create_tag_with_metadata(name, color, description, aliases) -> Tag`: Create structured tag
- `get_tag_info(tag_name) -> Optional[Dict]`: Get tag metadata
- `close() -> None`: Close storage connection

**Properties**:
- `storage`: SQLiteStorage instance
- `tag_manager`: TagManager instance
- `query_engine`: QueryEngine instance
- `recommender`: TagRecommender instance
- `plugin_manager`: PluginManager instance

## 4. Performance Specifications

### 4.1 Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Add task | < 5 ms | Single task insertion |
| List 1,000 tasks | < 10 ms | Full scan |
| Load from storage (1,000 tasks) | < 10 ms | Initial load |
| Simple query (1 tag) | < 20 ms | Single tag match |
| Complex query (3+ operators) | < 50 ms | Full evaluation |
| Create tag with metadata | < 10 ms | Per tag |
| Tag recommendation | < 20 ms | Per query |
| Concurrent writes (30 threads) | Safe | No corruption |

### 4.2 Scalability

- **Max tasks**: 100,000+ (tested with 10,000)
- **Max tags**: 1,000+ (tested with 500)
- **Max concurrent threads**: 30+ (tested with 30)
- **Database size**: ~10MB for 10,000 tasks
- **Memory overhead**: Minimal (load on demand)

## 5. Testing Strategy

### 5.1 Unit Tests

**StorageBackend**:
- Task CRUD operations
- Tag CRUD operations
- Co-occurrence tracking
- Concurrent operations
- Transaction safety

**TagManager**:
- Tag creation and metadata
- Alias resolution
- Usage tracking
- Co-occurrence recording
- Cache consistency

**QueryEngine**:
- Tokenization
- Parsing with precedence
- Evaluation logic
- Error handling
- Complex expressions

**Recommender**:
- Similarity scoring
- Co-occurrence ranking
- Task-based recommendations
- Keyword extraction

**PluginManager**:
- Hook registration
- Plugin loading
- Hook triggering
- Error handling

### 5.2 Integration Tests

- Backward compatibility API
- Persistence across instances
- Plugin hook execution
- End-to-end workflows

### 5.3 Performance Tests

- 1,000 task loading time
- Query latency
- Tag operation latency
- Concurrent operation safety

### 5.4 Stress Tests

- 30 concurrent threads
- 10,000 total tasks
- Complex query parsing
- High tag cardinality

## 6. File Organization

```
project_root/
├── todo_original.py                # Original (unchanged)
├── todo_advanced.py               # Public API wrapper
├── todo_advanced/                 # Main package
│   ├── __init__.py
│   ├── api.py
│   ├── storage.py
│   ├── tag_model.py
│   ├── query_engine.py
│   ├── recommender.py
│   └── plugin_manager.py
├── tests/
│   ├── __init__.py
│   └── test_advanced_todo.py
├── plugins/                       # Example plugins directory
│   ├── __init__.py
│   └── sample_plugin.py
├── perf_test.py                  # Performance validation
├── run_tests.ps1                 # Windows test runner
├── run_tests.sh                  # Unix test runner
├── requirements.txt              # Core dependencies
├── requirements-dev.txt          # Dev dependencies
├── README.md                     # User guide
├── FEATURE_SPEC.md              # This file
└── Prompt2.txt                   # Original prompt (for reference)
```

## 7. Error Handling

### 7.1 Storage Errors
- Database lock: Automatic retry with exponential backoff
- Schema errors: Clear migration instructions
- Corruption: Fallback to memory mode

### 7.2 Query Errors
- Syntax errors: Descriptive message with position
- Invalid operators: Clear error message
- Timeout: Return empty results after 5 seconds

### 7.3 Plugin Errors
- Load errors: Logged, plugin skipped
- Hook errors: Logged, execution continues
- Compatibility errors: Clear version mismatch message

## 8. Security Considerations

### 8.1 SQL Injection Prevention
- All queries use parameterized statements
- No string concatenation in SQL

### 8.2 Concurrency Safety
- No TOCTOU race conditions
- Atomic operations for critical sections
- Lock-based synchronization

### 8.3 Plugin Security
- Plugins run in same process (trusted execution)
- Hook exceptions don't crash system
- No privilege escalation

## 9. Future Extensions

### Potential Enhancements
1. **Full-text search**: Elasticsearch integration
2. **Cloud sync**: AWS S3 / Google Drive backup
3. **Collaborative**: Multi-user concurrent editing
4. **Webhooks**: External event notifications
5. **Custom backends**: PostgreSQL, MySQL support
6. **Advanced analytics**: Usage patterns, trends
7. **Mobile app**: REST API for mobile clients
8. **Voice commands**: Natural language queries
9. **Smart suggestions**: ML-based tag recommendations
10. **Task dependencies**: Subtasks and dependencies

## 10. Conclusion

This Advanced Tag System provides a robust, performant, and extensible enhancement to the minimal TODO application while maintaining complete backward compatibility. The modular architecture allows for future extensions without breaking existing code.

---

**Version**: 1.0.0
**Status**: Complete
**Last Updated**: December 2024
