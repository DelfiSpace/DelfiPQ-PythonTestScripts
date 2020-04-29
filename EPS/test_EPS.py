# EPS-specific test cases
import pytest
import PQ9Client
import time

# Global variables
pq9client = 0

@pytest.fixture(scope="module", autouse=True)
def do_something(request):
    global pq9client
    pq9client = PQ9Client.PQ9Client('localhost', 10000)
    pq9client.connect()
 
def finalizer_function():
    global pq9client
    pq9client.close()
        
def test_EPS():
    print("EPS ")