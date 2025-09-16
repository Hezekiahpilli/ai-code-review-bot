from src.review import _include

def test_globs():
    assert _include('app/main.py')
