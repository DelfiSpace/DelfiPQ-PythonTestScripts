# Test class to test the Ping service
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
    repeat = 1000
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
    
def test_PingWithExtraBytes(pq9_connection, destination):
    repeat = 254
    command = {}
    command["_send_"] = "SendRaw"
    command["dest"] = getAddress(destination)
    command["src"] = getAddress('EGSE')   
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
    
def getAddress(i):
   switcher={
      'OBC':'1',
      'EPS':'2',
      'ADB':'3',
      'COMMS':'4',
      'ADCS':'5',
      'PROP':'6',
      'DEBUG':'7',
      'EGSE':'8',
      'HPI':'100'
      }
   return switcher.get(i,0)
