# ADCS-specific test cases
import pytest
import sys
sys.path.insert(1, '../Generic')

import PQ9Client
import time
import json

@pytest.fixture(scope="session", autouse=True)
def do_something(request):
    global pq9client
    pq9client = PQ9Client.PQ9Client('localhost', 10000)
    pq9client.connect()
 
def finalizer_function():
    global pq9client
    pq9client.close()

def tff_PingWithExtraBytes(destination):
    global pq9client
    repeat = 254
    command = {}
    command["_send_"] = "SendRaw"
    command["dest"] = '5'
    command["src"] = '8'    
    count = 0
    startTime = time.time()
    for i in range(repeat):
        print(i)
        command["data"] = "17 1" + ( " 0" * i)
        #print(command)
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
       
    command = {}
    command["_send_"] = "GetTelemetry"
    command["Destination"] = "ADCS"
    command["Source"] = "EGSE"
    pq9client.sendFrame(command)
    succes, msg = pq9client.getFrame()
    assert succes == True, "Error: System is not responding"
    uptimeBeforeReset = int(json.loads(msg["Uptime"])["value"])
    if( uptimeBeforeReset < 3 ):
        time.sleep(3 - uptimeBeforeReset)
        pq9client.sendFrame(command)
        succes, msg = pq9client.getFrame()
        assert succes == True, "Error: System is not responding"
        uptimeBeforeReset = int(json.loads(msg["Uptime"])["value"])
    print("Uptime before reset:", uptimeBeforeReset, "s")
    
    command["_send_"] = "Reset"
    command["Destination"] = "ADCS"
    command["Source"] = "EGSE"
    command["Type"] = "Soft"
    pq9client.sendFrame(command)
    succes, msg = pq9client.getFrame()
    assert succes == True, "System is not responding"
    time.sleep(1)
    
    command["_send_"] = "GetTelemetry"
    command["Destination"] = "ADCS"
    command["Source"] = "EGSE"
    pq9client.sendFrame(command)
    succes, msg = pq9client.getFrame()
    assert succes == True, "Error: System is not responding"
    uptimeAfterReset = int(json.loads(msg["Uptime"])["value"])
    assert uptimeAfterReset < 2, "Error: Board did not reset"
    print("Uptime after reset:", uptimeAfterReset, "s")
    print("Soft Reset successful")
