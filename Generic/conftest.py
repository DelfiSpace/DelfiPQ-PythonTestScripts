# content of conftest.py
import pytest
import sys
import PQ9Client
import os
import PQ9TestSuite

def pytest_configure(config):
    print(config.getoption("--destination"))
    global destinationAddress
    if (config.getoption("--system") != None):
        destinationAddress = config.getoption("--system")
        config.option.htmlpath = destinationAddress + 'TestReport.html'
    else:
        destinationAddress = config.getoption("--destination")
        config.option.htmlpath = 'TestReport.html'
    
def pytest_ignore_collect(path, config):
    global destinationAddress
    if (config.getoption("--system") != None):
        #if (os.path.basename(path) == "test_ADCS.py"):
        return PQ9TestSuite.isTest(destinationAddress, os.path.basename(path))
    	#    return False
        #return True
    else:
        return False 

def pytest_addoption(parser):
    print("Option ")
    parser.addoption(
        "--destination", action="store", help="subsystem address", dest="destination",
    )
    parser.addoption(
        "--system", action="store", help="subsystem", dest="system",
    )
    
@pytest.fixture
def destination(request):
    global destinationAddress
    return destinationAddress

@pytest.fixture(scope="session") #only 'make' this object once per session.
def pq9_connection():
    pq9client = PQ9Client.PQ9Client("localhost","10000")
    pq9client.connect()

    yield pq9client
    pq9client.close()
