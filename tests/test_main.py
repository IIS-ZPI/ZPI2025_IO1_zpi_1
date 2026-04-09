from app.main import add, multiply

# Those tests are temporary to show work of automatic test system
# Should be removed later


def test_add():
    assert add(2, 3) == 5


def test_multiply():
    assert multiply(2, 3) == 6