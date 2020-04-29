# content of test_sysexit.py
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
        
def test_SoftReset(destination):
    global pq9client
    command = {}
    command["_send_"] = "Reset"
    command["Destination"] = destination
    command["Source"] = "EGSE"
    command["Type"] = "Soft"
    startTime = time.time()
    pq9client.sendFrame(command)
    succes, msg = pq9client.getFrame()
    elapsedTime = time.time() - startTime
    assert succes == True, "System is not responding"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    