import PQ9Client
import random
import json
import time

firstMsg = True
fileCount = 0
lineCount = 0
lastUptime = 0
MaxLines = 0
filename = "Telemetry_2_response_"+str(fileCount)+".csv"
fo = open(filename, 'w+')

class TelemetryExtractor:
    def __init__(self, startUptime, stopUptime):
        # does the addOne command 10x on one var, 10x on three vars.
        self.client = PQ9Client.PQ9Client("localhost","10000") # EGSE port
        self.client.connect()

        self.startUptime = startUptime
        self.stopUptime = stopUptime

        self.firstMsg = True
        self.fileCount = 0
        self.lineCount = 0
        self.lastUptime = 0
        self.MaxLines = 24*3600
        self.filename = "Telemetry_2_response_"+str(fileCount)+".csv"
        self.fo = open(filename, 'w+')

    def run(self):
        for i in range(self.startUptime, self.stopUptime):
            print("Getting Uptime: ", end="")
            targetBytes = i.to_bytes(4, byteorder="big")
            targetBytes = list(targetBytes)
            print(targetBytes)
            command = {}
            command["_send_"] = "SendRaw"
            command["dest"] = "1" # OBC
            command["src"] = "8"
            command["data"] = "123 1 2 "+" ".join(str(item) for item in targetBytes) # Ping Request
            # print(command)
            self.client.sendFrame(command)
            succes, msg = self.client.getFrame()
            if( succes and json.loads(msg['_raw_'])[3] == 3):
                self.logTelemetry(msg)

        print("Done!")

    def logTelemetry(self, msg):
        # print(msg)
        # Parse Reply into CSV String
        if(self.firstMsg):
            nameString = ""
            for jObj in msg:
                nameString += str(jObj) + ","
            nameString = nameString[:-1] + "\n"
            print(nameString)
            self.firstMsg = False
            self.fo.write(nameString)

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
            # print("New Telemetry found!")
            self.lastUptime = json.loads(msg["Uptime"])["value"]
            self.fo.write(valueString)
            self.lineCount += 1
            if(self.lineCount >= self.MaxLines):
                self.fileCount += 1
                filename = "Telemetry_2_response_"+str(fileCount)+".csv"
                self.fo = open(filename, 'w+')
                self.lineCount = 0
                self.firstMsg = True 


if __name__ == "__main__":
    extractor = TelemetryExtractor(1,80000)
    TelemetryExtractor.run(extractor)
