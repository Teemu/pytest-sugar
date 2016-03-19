import pytest

@pytest.mark.skip
def test_skip_this_one():
    assert True

@pytest.mark.skip
def test_skip_this_one_as_well():
    assert True

@pytest.mark.skipif(True, reason='This must be skipped.')
def test_skip_this_if():
    assert True

def test_dont_skip_this_one():
    assert True
