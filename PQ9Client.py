import asyncio
import json

class PQ9Client:

    def __init__(self):
        super().__init__()
        TCP_IP = 'localhost'
        TCP_PORT = 10000
        self.pq9reader = 0
        self.pq9writer = 0
        self.loop = 0

    def close(self):
        asyncio.run(self.AwaitedClose())

    async def AwaitedClose(self):
        self.pq9reader.close()
        self.pq9writer.close()
        await self.pq9writer.wait_closed()
        await self.pq9reader.wait_closed()
    
    def connect(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.AwaitedConnect())

    async def AwaitedConnect(self):
        TCP_IP = 'localhost'
        TCP_PORT = 10000
        self.pq9reader, self.pq9writer = await asyncio.open_connection(TCP_IP, TCP_PORT, loop=self.loop)
        print("PQ9Socket: Connected to localhost:10000")

    def sendFrame(self, inputFrame):
        self.loop.run_until_complete(self.AwaitedSendFrame(inputFrame))

    async def AwaitedSendFrame(self,inputFrame):
        cmdString = json.dumps(inputFrame) + '\n'
        #print("Sending: "+cmdString, end="")
        self.pq9writer.write(cmdString.encode())
        await self.pq9writer.drain()

    def getFrame(self):
        status, msg = self.loop.run_until_complete(self.AwaitedGetFrame())
        if(status == True):
            # return status, json.loads(msg)["_raw_"]
            return status, json.loads(msg)
        else:
            return status, []

    async def AwaitedGetFrame(self):
        try:
            rxMsg = await asyncio.wait_for(self.pq9reader.readline(), timeout=2)
            return True, rxMsg
        except asyncio.TimeoutError:
            print("PQ9EGSE Reply Timeout!")
            return False, []

    def processCommand(self, command):
        self.sendFrame(command)
        succes, msg = self.getFrame()
        if(succes == False):
            print("PQ9EGSE Reply Timeout!")
            return False, []
        else:
            while((json.loads((msg["_raw_"]))[2] == (command["dest"]).split()[0]) and  #if the destination == source and service == service
                (json.loads((msg["_raw_"]))[3] == (command["data"]).split()[0])):
                succes, msg = self.getFrame()
                if(succes == False):
                    print("PQ9EGSE Reply Timeout!")
                    return False, []
            return succes, msg