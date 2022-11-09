import pytest


@pytest.fixture
def fixt():
    raise Exception
    yield


def test_foo(fixt):
    pass
