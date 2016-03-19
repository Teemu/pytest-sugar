import pytest

COUNT = 0

@pytest.mark.flaky(reruns=10)
def test_flaky_test():
    global COUNT
    COUNT += 1
    assert COUNT >= 7
