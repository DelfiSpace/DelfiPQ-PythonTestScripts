import PQ9Client
import json
import sys
import time
import os

if __name__ == "__main__":
    pq9client = PQ9Client.PQ9Client()
    pq9client.connect()

    comPortName = sys.argv[1] # "tty.usbserial-AH3YB5A0" #
    dest = sys.argv[2]
    # inputFileName = sys.argv[3]
    print("Connecting PC_EGSE to COMPORT: "+comPortName)
    command = {}
    command["command"] = "reloadSerialPorts"
    pq9client.sendFrame(command)
    command["command"] = "setSerialPort"
    command["data"] = comPortName
    pq9client.sendFrame(command)

    time.sleep(2)
    
    # print("Opening file: "+inputFileName)
    # fi = open(inputFileName, "r")
    # try:
    #     os.remove("Telemetry_"+str(dest)+"_response.csv")
    # except:
    #     pass

    filename = "Telemetry_"+str(dest)+"_response.csv"
    fo = open(filename, 'w+')
    lastUptime = 0
    firstMsg = True 

    # for commandline in commandlines:
    while True:
        command = {}
        command["_send_"] = "SendRaw"
        command["dest"] = dest
        command["src"] = "1"
        command["data"] = "3 1" # Telemetry Request
        pq9client.sendFrame(command)
        succes, msg = pq9client.getFrame()
        if(succes):
            if(json.loads((msg["_raw_"]))[3] == 3): #houseKeeping reply
                # print(msg)
                # Parse Reply into CSV String
                if(firstMsg):
                    nameString = ""
                    for jObj in msg:
                        nameString += str(jObj) + ","
                    nameString = nameString[:-1] + "\n"
                    print(nameString)
                    firstMsg = False
                    fo.write(nameString)

                if(json.loads(msg["Uptime"])["value"] != lastUptime ):
                    # print("new Block!")
                    valueString = ""
                    for jObj in msg:
                        # print(jObj+"  -  ", end="")
                        jValue = msg[jObj]
                        # print(jValue)
                        try:
                            if (str(jObj) == "_raw_" ):
                                valueString += "\""+str(json.loads(jValue)["value"])+"\"" + ","
                            else:
                                valueString += str(json.loads(jValue)["value"]) + ","
                        except:
                            if (str(jObj) == "_raw_" ):
                                valueString += "\""+str(jValue)+"\"" + ","
                            else:
                                valueString += "\""+str(jValue)+"\"" + ","
                    valueString = valueString[:-1] + "\n"
                    # print(valueString)
                    print("New Telemetry found!")
                    lastUptime = json.loads(msg["Uptime"])["value"]
                    fo.write(valueString)

                time.sleep(0.8)

        else:
            "No Response±!!"
            break