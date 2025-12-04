from todo_advanced.api import add_todo, set_tag_metadata, get_tag, tag_cooccurrence


def test_tag_meta_and_cooccurrence():
    add_todo('m1', tags=['alpha', 'beta'])
    add_todo('m2', tags=['alpha', 'gamma'])
    set_tag_metadata('alpha', color='blue', description='alpha tag')
    t = get_tag('alpha')
    assert t is not None
    assert t['color'] == 'blue'
    co = tag_cooccurrence('alpha')
    assert 'beta' in co
    assert 'gamma' in co
