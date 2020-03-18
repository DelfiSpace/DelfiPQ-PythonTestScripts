import PQ9Client
import sys
import time

if __name__ == "__main__":
    pq9client = PQ9Client.PQ9Client()
    pq9client.connect()

    comPortName = sys.argv[1]
    dest = sys.argv[2]
    inputFileName = sys.argv[3]
    print("Connecting PC_EGSE to COMPORT: "+comPortName)
    command = {}
    command["command"] = "reloadSerialPorts"
    pq9client.sendFrame(command)
    command["command"] = "setSerialPort"
    command["data"] = comPortName
    pq9client.sendFrame(command)

    time.sleep(3)
    
    print("Opening file: "+inputFileName)
    fi = open(inputFileName, "r")
    fo = open(inputFileName+"_response", 'w')
    commandlines = fi.readlines()
    for commandline in commandlines:
        command = {}
        command["_send_"] = "SendRaw"
        command["dest"] = dest
        command["src"] = "1"
        command["data"] = commandline.rstrip("\n")
        pq9client.sendFrame(command)
        succes, msg = pq9client.getFrame()
        if(succes):
            print(msg)
            fo.write(msg.replace('[','').replace(']','').replace(',','') + '\n' )
        else:
            break