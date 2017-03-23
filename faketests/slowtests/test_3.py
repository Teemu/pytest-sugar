import time
import pytest

@pytest.mark.parametrize("index", range(7))
def test_cat(index):
    """Perform several tests with varying execution times."""
    time.sleep(0.2 + (index * 0.1))
    assert True
