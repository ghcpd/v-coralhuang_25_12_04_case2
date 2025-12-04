def test_module_imports():
    import todo_advanced_pkg.cache as c
    import todo_advanced_pkg.validation as v
    assert c.SimpleCache() is not None
    assert v.validate_tag_name("ok_tag")
