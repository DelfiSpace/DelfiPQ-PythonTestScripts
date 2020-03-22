import sys
import time
import json
import PQ9Client
from queue import Queue
from PySide2.QtWidgets import *
from PySide2.QtCore import *

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QFillBox(QWidget):
    def __init__(self, label, defaultVal):
        super().__init__()
        self.label = QLabel(label)
        self.text = QLineEdit()
        self.text.setText(str(defaultVal))
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class PQ9CommandHandler(QRunnable):
    def __init__(self, *args, **kwargs):
        super(PQ9CommandHandler, self).__init__(*args, **kwargs)
        self.getTelemetry = False
        self.stopSignal = False
        self.commandQueue = Queue()
        self.busStates = [True, False, False, False]
        self.pq9client = PQ9Client.PQ9Client()
        self.pq9client.connect()

        self.MaxLines = 24*3600
        self.fileCount = 0
        filename = "Telemetry_2_response_"+str(self.fileCount)+".csv"
        self.fo = open(filename, 'w+')
        self.lineCount = 0
        self.firstMsg = True 
        self.lastUptime = 0


        self.autoToggleEnabled = [False, False, False, False]
        self.autoToggleOnTime = [10, 10, 10, 10]
        self.autoToggleOffTime = [10, 10, 10, 10]
        self.autoToggleStartTime = [0, 0, 0, 0]



    def toggleAutoToggle(self, state, toggleTarget, onTime, offTime):
        print("OnTime: "+str(onTime))
        print("OffTime: "+str(offTime))
        self.autoToggleEnabled[toggleTarget-1] = state
        self.autoToggleStartTime[toggleTarget-1] = time.time()
        self.autoToggleOnTime[toggleTarget-1] = onTime
        self.autoToggleOffTime[toggleTarget-1] = offTime
        if(state):
            print("AutoToggle Enabled for: ", end ="")
            print(toggleTarget)
            if(self.busStates[toggleTarget-1] == False):
                self.toggleBusCmd(toggleTarget)
        else:
            print("AutoToggle Disabled")

    def toggleTelemetry(self, state):
        self.getTelemetry = state
        

    def toggleBusCmd(self, busNr):
        print("Toggle Bus "+str(busNr) + ((" OFF") if self.busStates[busNr-1] else (" ON")))
        #Queue command
        command = {}
        command["_send_"] = "SendRaw"
        command["dest"] = "2" # EPS
        command["src"] = "8"
        command["data"] = "1 1 "+str(busNr)+ (" 0" if self.busStates[busNr-1] else " 1") # PowerBus Request
        self.commandQueue.put(command)
        self.busStates[busNr-1] = not self.busStates[busNr-1]

    def logTelemetry(self, msg):
        if(json.loads((msg["_raw_"]))[3] == 3): #houseKeeping reply
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

            if(json.loads(msg["Uptime"])["value"] != self.lastUptime ):
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
                self.lastUptime = json.loads(msg["Uptime"])["value"]
                self.fo.write(valueString)
                self.lineCount += 1
                if(self.lineCount >= self.MaxLines):
                    self.fileCount += 1
                    filename = "Telemetry_2_response_"+str(self.fileCount)+".csv"
                    self.fo = open(filename, 'w+')
                    self.lineCount = 0
                    self.firstMsg = True 

    @Slot()
    def run(self):
        while True:
            try:
                if(self.stopSignal):
                    return

                for i in range(0,4):
                    if(self.autoToggleEnabled[i]):
                        elapsedTime = time.time() - self.autoToggleStartTime[i]
                        # print(elapsedTime)
                        #print(str(elapsedTime) + "  -  ", end = "")
                        #print(self.autoToggleOnTime)
                        if(elapsedTime > (self.autoToggleOffTime[i] + self.autoToggleOnTime[i])) :
                            #turn devices on
                            self.autoToggleStartTime[i] = time.time()
                            if(self.busStates[i] == False):
                                self.toggleBusCmd(i+1)
                        elif(elapsedTime > self.autoToggleOnTime[i]):
                            #print("turn off!")
                            if(self.busStates[i] == True):
                                self.toggleBusCmd(i+1)
                                #turn devices off

                while(not self.commandQueue.empty()):
                    #command Queue is not empty! so run commands
                    command = self.commandQueue.get()
                    succes, msg = self.pq9client.processCommand(command)
                
                if(self.getTelemetry):
                    command = {}
                    command["_send_"] = "SendRaw"
                    command["dest"] = "2" # EPS
                    command["src"] = "8"
                    command["data"] = "3 1"
                    succes, msg = self.pq9client.processCommand(command)
                    if(succes):
                        self.logTelemetry(msg)

                time.sleep(.1)
            except:
                pass
                time.sleep(.5)
    

class EPSTestingGui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(EPSTestingGui, self).__init__(*args, **kwargs)
        self.threadpool = QThreadPool()
        self.cmdHandler = PQ9CommandHandler()
        self.threadpool.start(self.cmdHandler)
        self.setWindowTitle("DelfiPQ EPS Testing Tool")

        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        reconnectButton = QPushButton("Reconnect to EGSE")
        reconnectButton.pressed.connect(self.reconnectEGSE)

        self.comportSelect = QFillBox("COM port:", "COM3")
        comportButton = QPushButton("Connect SerialPort")
        comportButton.pressed.connect(self.reconnectSerial)

        telemetryWidget = QWidget()
        telemetryLayout = QVBoxLayout()
        telemetryWidget.setLayout(telemetryLayout)
        telemetryWidgetLabel = QLabel("Telemetry Logging Control")
        telemetryWidgetLabel.setAlignment(Qt.AlignHCenter)
        telemetryLayout.addWidget(telemetryWidgetLabel)
        tele_start = QPushButton("START TELEMETRY LOGGING")
        tele_stop = QPushButton("STOP TELEMETRY LOGGING")
        tele_start.pressed.connect(self.startTelemetryCollect)
        tele_stop.pressed.connect(self.stopTelemetryCollect)
        tele_buttonLayout = QHBoxLayout()
        tele_buttonLayout.addWidget(tele_start)
        tele_buttonLayout.addWidget(tele_stop)
        tele_buttonWidget = QWidget()
        tele_buttonWidget.setLayout(tele_buttonLayout)
        telemetryLayout.addWidget(tele_buttonWidget)

        busControlWidget = QWidget()
        busControlLayout = QVBoxLayout()
        busControlWidget.setLayout(busControlLayout)
        busControlLabel = QLabel("Manual Bus Toggle")
        busControlLabel.setAlignment(Qt.AlignHCenter)
        busControlLayout.addWidget(busControlLabel)
        bus_1_toggle = QPushButton("BUS1")
        bus_2_toggle = QPushButton("BUS2")
        bus_3_toggle = QPushButton("BUS3")
        bus_4_toggle = QPushButton("BUS4")
        bus_1_toggle.pressed.connect(lambda x=1: self.toggleBus(x))
        bus_2_toggle.pressed.connect(lambda x=2: self.toggleBus(x))
        bus_3_toggle.pressed.connect(lambda x=3: self.toggleBus(x))
        bus_4_toggle.pressed.connect(lambda x=4: self.toggleBus(x))
        bus_toggleLayout = QHBoxLayout()
        bus_toggleLayout.addWidget(bus_1_toggle)
        bus_toggleLayout.addWidget(bus_2_toggle)
        bus_toggleLayout.addWidget(bus_3_toggle)
        bus_toggleLayout.addWidget(bus_4_toggle)
        bus_toggleWidget = QWidget()
        bus_toggleWidget.setLayout(bus_toggleLayout)
        busControlLayout.addWidget(bus_toggleWidget)

        bus1ControlAutoWidget = QWidget()
        bus1ControlAutoLayout = QVBoxLayout()
        bus1ControlAutoWidget.setLayout(bus1ControlAutoLayout)
        self.bus1_offtime = QFillBox("OFF Time [sec]", 10)
        self.bus1_ontime = QFillBox("ON Time [sec]", 10)
        bus1_auto_start = QPushButton("START")
        bus1_auto_stop = QPushButton("STOP")
        bus1_auto_start.pressed.connect(lambda x=True, target=1: self.toggleAutoToggle(x, target))
        bus1_auto_stop.pressed.connect(lambda x=False, target=1: self.toggleAutoToggle(x, target))
        bus1_toggle_autoLayout = QGridLayout()
        bus1_toggle_autoLayout.addWidget(self.bus1_offtime,0,2,1,2)
        bus1_toggle_autoLayout.addWidget(self.bus1_ontime,0,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus1_auto_start,1,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus1_auto_stop,1,2,1,2)
        bus1_toggle_autoWidget = QWidget()
        bus1_toggle_autoWidget.setLayout(bus1_toggle_autoLayout)
        bus1ControlAutoLayout.addWidget(bus1_toggle_autoWidget)

        bus2ControlAutoWidget = QWidget()
        bus2ControlAutoLayout = QVBoxLayout()
        bus2ControlAutoWidget.setLayout(bus2ControlAutoLayout)
        self.bus2_offtime = QFillBox("OFF Time [sec]", 10)
        self.bus2_ontime = QFillBox("ON Time [sec]", 10)
        bus2_auto_start = QPushButton("START")
        bus2_auto_stop = QPushButton("STOP")
        bus2_auto_start.pressed.connect(lambda x=True, target=2: self.toggleAutoToggle(x, target))
        bus2_auto_stop.pressed.connect(lambda x=False, target=2: self.toggleAutoToggle(x, target))
        bus2_toggle_autoLayout = QGridLayout()
        bus1_toggle_autoLayout.addWidget(self.bus2_offtime,2,2,1,2)
        bus1_toggle_autoLayout.addWidget(self.bus2_ontime,2,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus2_auto_start,3,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus2_auto_stop,3,2,1,2)
        bus2_toggle_autoWidget = QWidget()
        bus2_toggle_autoWidget.setLayout(bus2_toggle_autoLayout)
        bus2ControlAutoLayout.addWidget(bus2_toggle_autoWidget)

        bus3ControlAutoWidget = QWidget()
        bus3ControlAutoLayout = QVBoxLayout()
        bus3ControlAutoWidget.setLayout(bus3ControlAutoLayout)
        self.bus3_offtime = QFillBox("OFF Time [sec]", 10)
        self.bus3_ontime = QFillBox("ON Time [sec]", 10)
        bus3_auto_start = QPushButton("START")
        bus3_auto_stop = QPushButton("STOP")
        bus3_auto_start.pressed.connect(lambda x=True, target=3: self.toggleAutoToggle(x, target))
        bus3_auto_stop.pressed.connect(lambda x=False, target=3: self.toggleAutoToggle(x, target))
        bus3_toggle_autoLayout = QGridLayout()
        bus1_toggle_autoLayout.addWidget(self.bus3_offtime,4,2,1,2)
        bus1_toggle_autoLayout.addWidget(self.bus3_ontime,4,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus3_auto_start,5,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus3_auto_stop,5,2,1,2)
        bus3_toggle_autoWidget = QWidget()
        bus3_toggle_autoWidget.setLayout(bus3_toggle_autoLayout)
        bus3ControlAutoLayout.addWidget(bus3_toggle_autoWidget)

        bus4ControlAutoWidget = QWidget()
        bus4ControlAutoLayout = QVBoxLayout()
        self.bus4_offtime = QFillBox("OFF Time [sec]", 10)
        self.bus4_ontime = QFillBox("ON Time [sec]", 10)
        bus4_auto_start = QPushButton("START")
        bus4_auto_stop = QPushButton("STOP")
        bus4_auto_start.pressed.connect(lambda x=True, target=4: self.toggleAutoToggle(x, target))
        bus4_auto_stop.pressed.connect(lambda x=False, target=4: self.toggleAutoToggle(x, target))
        bus4_toggle_autoLayout = QGridLayout()
        bus1_toggle_autoLayout.addWidget(self.bus4_offtime,6,2,1,2)
        bus1_toggle_autoLayout.addWidget(self.bus4_ontime,6,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus4_auto_start,7,0,1,2)
        bus1_toggle_autoLayout.addWidget(bus4_auto_stop,7,2,1,2)
        bus4_toggle_autoWidget = QWidget()
        bus4_toggle_autoWidget.setLayout(bus4_toggle_autoLayout)
        bus4ControlAutoLayout.addWidget(bus4_toggle_autoWidget)

        layout = QVBoxLayout()
        layout.addWidget(reconnectButton)
        layout.addWidget(self.comportSelect)
        layout.addWidget(comportButton)
        layout.addWidget(QHLine())
        layout.addWidget(telemetryWidget)
        layout.addWidget(QHLine())
        layout.addWidget(busControlWidget)
        layout.addWidget(QHLine())
        layout.addWidget(bus1ControlAutoWidget)
        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

    def toggleAutoToggle(self, state, toggleTarget):
        if(toggleTarget == 1):
            self.cmdHandler.toggleAutoToggle(state, toggleTarget, float(self.bus1_ontime.text.text()), float(self.bus1_offtime.text.text()))
        if(toggleTarget == 2):
            self.cmdHandler.toggleAutoToggle(state, toggleTarget, float(self.bus2_ontime.text.text()), float(self.bus2_offtime.text.text()))
        if(toggleTarget == 3):
            self.cmdHandler.toggleAutoToggle(state, toggleTarget, float(self.bus3_ontime.text.text()), float(self.bus3_offtime.text.text()))
        if(toggleTarget == 4):
            self.cmdHandler.toggleAutoToggle(state, toggleTarget, float(self.bus4_ontime.text.text()), float(self.bus4_offtime.text.text()))

    def reconnectEGSE(self):
        try:
            self.cmdHandler.pq9client.close()
        except:
            pass
        # self.cmdHandler.stopSignal = True
        # self.cmdHandler = PQ9CommandHandler()
        self.cmdHandler.pq9client.connect()

    def reconnectSerial(self):
        print("Connecting PC_EGSE to COMPORT: "+self.comportSelect.text.text())
        command = {}
        command["command"] = "reloadSerialPorts"
        self.cmdHandler.pq9client.sendFrame(command)
        command["command"] = "setSerialPort"
        command["data"] = self.comportSelect.text.text()
        self.cmdHandler.pq9client.sendFrame(command)

    def closeEvent(self, event):
        print("Closing cmdHandler")
        self.cmdHandler.stopSignal = True

    def startTelemetryCollect(self):
        self.cmdHandler.toggleTelemetry(True)

    def stopTelemetryCollect(self):
        self.cmdHandler.toggleTelemetry(False)

    def toggleBus(self, BusNR):
        self.cmdHandler.toggleBusCmd(BusNR)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EPSTestingGui()
    window.show()

    app.exec_()
