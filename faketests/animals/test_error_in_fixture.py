import pytest

@pytest.fixture
def example():
    raise Exception("Error")

def test_error_in_fixture(example):
    assert True
