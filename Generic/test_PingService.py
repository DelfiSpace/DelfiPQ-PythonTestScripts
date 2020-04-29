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
        
def test_SinglePing(destination):
    global pq9client
    command = {}
    command["_send_"] = "Ping"
    command["Destination"] = destination
    command["Source"] = "EGSE"
    startTime = time.time()
    pq9client.sendFrame(command)
    succes, msg = pq9client.getFrame()
    elapsedTime = time.time() - startTime
    assert succes == True, "System is not responding"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    
def test_MultiplePing(destination):
    global pq9client
    repeat = 1000
    command = {}
    command["_send_"] = "Ping"
    command["Destination"] = destination
    command["Source"] = "EGSE"
    count = 0
    startTime = time.time()
    for i in range(repeat):
        pq9client.sendFrame(command)
        succes, msg = pq9client.getFrame()
        count+= 1
    elapsedTime = time.time() - startTime
    assert count == repeat, "Missing reponses"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    print("Responses ", count)
    
def test_PingWithExtraBytes(destination):
    global pq9client
    repeat = 254
    command = {}
    command["_send_"] = "SendRaw"
    command["dest"] = '1'
    command["src"] = '2'    
    count = 0
    startTime = time.time()
    for i in range(repeat):
        command["data"] = "17 1" + ( " 0" * i)
        pq9client.sendFrame(command)
        succes, msg = pq9client.getFrame()
        #report if one frame is missing
        if (succes != True):
        	print("Frame", i, "not received")
        	print(command)     
        count+= 1
    elapsedTime = time.time() - startTime
    assert count == repeat, "Missing reponses"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    print("All Ping requests received")