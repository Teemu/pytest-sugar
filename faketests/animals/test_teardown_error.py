import pytest


@pytest.fixture
def fixt():
    yield
    raise Exception


def test_foo(fixt):
    pass
