from todo_advanced.query import query
from todo_advanced.api import add_todo


def test_query_and_or_not():
    add_todo('q1', tags=['work', 'urgent'])
    add_todo('q2', tags=['work'])
    add_todo('q3', tags=['personal'])
    res = query('tag:work AND NOT tag:urgent')
    assert any(r['task']=='q2' for r in res)
    assert all('work' in r['tags'] for r in res)

    res2 = query('work OR personal')
    assert len(res2) >= 3
