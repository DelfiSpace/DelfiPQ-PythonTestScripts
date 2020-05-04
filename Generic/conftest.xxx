# content of conftest.py
import pytest
import PQ9Client

def pytest_addoption(parser):
    parser.addoption(
        "--destination", action="store", help="subsystem address", dest="destination",
    )
@pytest.fixture
def destination(request):
    return request.config.getoption("--destination")

@pytest.fixture(scope="session") #only 'make' this object once per session.
def pq9_connection():
    pq9client = PQ9Client.PQ9Client("localhost","10000")
    pq9client.connect()

    yield pq9client
    pq9client.close()
