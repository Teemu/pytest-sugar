import pytest


@pytest.mark.xfail
def test_xfail_true():
    assert True


@pytest.mark.xfail
def test_xfail_false():
    assert False


@pytest.mark.xfail
def test_xpass_true():
    assert True


@pytest.mark.xfail
def test_xpass_false():
    assert False


@pytest.mark.xfail(strict=True)
def test_strict_xfail_true():
    assert True


@pytest.mark.xfail(strict=False)
def test_strict_xfail_false():
    assert False


@pytest.mark.xfail(strict=True)
def test_strict_xpass_true():
    assert True


@pytest.mark.xfail(strict=False)
def test_strict_xpass_false():
    assert False
