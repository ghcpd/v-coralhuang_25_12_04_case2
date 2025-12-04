import os
import importlib
import pytest
from todo_advanced_pkg.query import QueryEngine, parse_expression, ParseError
import todo_advanced
import todo_advanced_pkg


def test_query_engine_basic(tmp_path, monkeypatch):
    db_file = tmp_path / "q.db"
    monkeypatch.setenv("TODO_DB", str(db_file))
    importlib.reload(todo_advanced_pkg.backend)
    todo_advanced_pkg.backend._backend_singleton = None
    backend = todo_advanced.get_backend()
    assert backend is not None
    backend.add_todo("T1", tags=["work", "urgent"])
    backend.add_todo("T2", tags=["work"])
    backend.add_todo("T3", tags=["personal"])
    qe = QueryEngine(backend)
    res = qe.query("tag:work AND NOT tag:urgent")
    assert len(res) == 1 and res[0]["task"] == "T2"
    res2 = qe.query("tag:work AND (tag:urgent OR tag:personal)")
    assert set(t["task"] for t in res2) == {"T1"}


def test_parse_errors():
    with pytest.raises(ParseError):
        parse_expression("tag:work AND OR")
    with pytest.raises(ParseError):
        parse_expression("(tag:work")
