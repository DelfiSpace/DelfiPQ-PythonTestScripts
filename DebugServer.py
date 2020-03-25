import socket
from threading import Thread
from serial import Serial

class DebugServer:

    def handle_clients(self):
        self.sock.listen(5)                 # Now wait for client connection.
        while True:
            c, addr = self.sock.accept()     # Establish connection with client.
            self.connections.append(c)
            print("New Connection!")

    def handle_serial(self):
        while True:
            if self.ser.inWaiting() > 0:
                line = self.ser.readline()
                print(line)
                for con in self.connections:
                    try:
                        con.sendall(line)
                    except:
                        print("client disconnected?")
                        self.connections.remove(con)
        self.handle_serial()


    def __init__(self):
        self.ser = Serial('COM3', timeout=0.1)
        self.writers = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 20000)
        self.sock.bind(server_address)
        self.connections = []

        threads = []
        hc_thread = Thread(target=self.handle_clients)
        ser_thread = Thread(target=self.handle_serial)
        threads.append(hc_thread)
        threads.append(ser_thread)

        for t in threads:
            t.start()
        for t in threads:  # shut down cleanly
            t.join()
        

    async def run(self):
        while True:
            if self.ser.inWaiting() > 0:
                line = self.ser.readline()
                print(line)

if __name__ == "__main__":
    serv = DebugServer()
    #asyncio.run(serv.run())