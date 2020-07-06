# content of conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--destination", action="store", help="subsystem address"
    )

@pytest.fixture
def destination(request):
    return request.config.getoption("--destination")
