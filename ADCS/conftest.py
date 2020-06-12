# content of conftest.py
import pytest
import sys
sys.path.insert(1, '../Generic')
import PQ9Client
    
def pytest_configure(config):
    print("pytest_configure")
    
def pytest_collection_modifyitems(session, config, items):
    print("sono qui", items)
    
def pytest_ignore_collect(path, config):
    print(path)
    print("mamma ", config.getoption("--destination"))
    return False 

def pytest_addoption(parser):
    print("Option ")
    parser.addoption(
        "--destination", action="store", help="subsystem address", dest="destination",
    )
@pytest.fixture
def destination(request):
    print(request.config.getoption("--html"))
    #print(request.config.getoption("kkk"))
    return request.config.getoption("--destination")

@pytest.fixture(scope="session") #only 'make' this object once per session.
def pq9_connection():
    pq9client = PQ9Client.PQ9Client("localhost","10000")
    pq9client.connect()

    yield pq9client
    pq9client.close()
