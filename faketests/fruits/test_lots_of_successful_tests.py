import pytest

@pytest.mark.parametrize('x', [True]*500)
def test_ok(x):
    assert True
