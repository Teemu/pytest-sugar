import time
import pytest

@pytest.mark.parametrize("index", range(7))
def test_cat(index):
    """Perform several tests with the same execution times."""
    time.sleep(0.4)
    assert True
