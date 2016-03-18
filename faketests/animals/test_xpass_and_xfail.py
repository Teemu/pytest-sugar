import pytest

@pytest.mark.xfail
def test_xfail_true():
    assert True

@pytest.mark.xfail
def test_xfail_false():
    assert False

@pytest.mark.xpass
def test_xpass_true():
    assert True

@pytest.mark.xpass
def test_xpass_false():
    assert False
