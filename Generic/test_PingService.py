# content of test_sysexit.py
import pytest
import PQ9Client
import time

def test_SinglePing(pq9_connection, destination):
    command = {}
    command["_send_"] = "Ping"
    command["Destination"] = destination
    command["Source"] = "EGSE"
    startTime = time.time()
    succes, msg = pq9_connection.processCommand(command)
    elapsedTime = time.time() - startTime
    assert succes == True, "System is not responding"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    
def test_MultiplePing(pq9_connection, destination):
    repeat = 10
    command = {}
    command["_send_"] = "Ping"
    command["Destination"] = destination
    command["Source"] = "EGSE"
    count = 0
    startTime = time.time()
    for i in range(repeat):
        succes, msg = pq9_connection.processCommand(command)
        count+= 1
    elapsedTime = time.time() - startTime
    assert count == repeat, "Missing reponses"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    print("Responses ", count)
    
def est_PingWithExtraBytes(pq9_connection, destination):
    repeat = 254
    command = {}
    command["_send_"] = "SendRaw"
    command["dest"] = '2'
    command["src"] = '8'    
    count = 0
    startTime = time.time()
    for i in range(repeat):
        command["data"] = "17 1" + ( " 0" * i)
        succes, msg = pq9_connection.processCommand(command)
        #report if one frame is missing
        if (succes != True):
        	print("Frame", i, "not received")
        	print(command)     
        count+= 1
    elapsedTime = time.time() - startTime
    assert count == repeat, "Missing reponses"
    print("Elapsed time: ", round(elapsedTime * 1000, 0), " ms")
    print("All Ping requests received")
