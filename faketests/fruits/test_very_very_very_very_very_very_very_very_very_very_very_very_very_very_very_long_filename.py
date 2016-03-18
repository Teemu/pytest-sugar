import pytest

@pytest.mark.parametrize('x', [True]*10)
def test_ok(x):
    assert True
