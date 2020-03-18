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

        filename = "Telemetry_2_response.csv"
        self.fo = open(filename, 'w+')
        self.lastUptime = 0
        self.firstMsg = True 

        self.autoToggleEnabled = False
        self.autoToggleTargetList = []
        self.autoToggleOnTime = 10
        self.autoToggleOffTime = 10
        self.autoToggleStartTime = 0



    def toggleAutoToggle(self, state, toggleList, onTime, offTime):
        self.autoToggleEnabled = state
        self.autoToggleStartTime = time.time()
        self.autoToggleTargetList = toggleList
        self.autoToggleOnTime = onTime
        self.autoToggleOffTime = offTime
        if(state):
            print("AutoToggle Enabled for: ", end ="")
            print(self.autoToggleTargetList)
            for target in self.autoToggleTargetList:
                if(self.busStates[target-1] == False):
                    self.toggleBusCmd(target)
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
        command["src"] = "1"
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

    @Slot()
    def run(self):
        while True:
            if(self.stopSignal):
                return

            if(self.autoToggleEnabled):
                elapsedTime = time.time() - self.autoToggleStartTime
                #print(str(elapsedTime) + "  -  ", end = "")
                #print(self.autoToggleOnTime)
                if(elapsedTime > (self.autoToggleOffTime + self.autoToggleOnTime)) :
                    #turn devices on
                    self.autoToggleStartTime = time.time()
                    for target in self.autoToggleTargetList:
                        if(self.busStates[target-1] == False):
                            self.toggleBusCmd(target)
                elif(elapsedTime > self.autoToggleOnTime):
                    for target in self.autoToggleTargetList:
                        if(self.busStates[target-1] == True):
                            self.toggleBusCmd(target)
                        #turn devices off

            while(not self.commandQueue.empty()):
                #command Queue is not empty! so run commands
                command = self.commandQueue.get()
                succes, msg = self.pq9client.processCommand(command)
            
            if(self.getTelemetry):
                command = {}
                command["_send_"] = "SendRaw"
                command["dest"] = "2" # EPS
                command["src"] = "1"
                command["data"] = "3 1"
                succes, msg = self.pq9client.processCommand(command)
                if(succes):
                    self.logTelemetry(msg)

            time.sleep(.1)
    

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

        busControlAutoWidget = QWidget()
        busControlAutoLayout = QVBoxLayout()
        busControlAutoWidget.setLayout(busControlAutoLayout)
        busControlAutoLabel = QLabel("Automatic Bus Toggle")
        busControlAutoLabel.setAlignment(Qt.AlignHCenter)
        busControlAutoLayout.addWidget(busControlAutoLabel)
        self.bus_1_toggle_auto = QCheckBox("BUS1")
        self.bus_2_toggle_auto = QCheckBox("BUS2")
        self.bus_3_toggle_auto = QCheckBox("BUS3")
        self.bus_4_toggle_auto = QCheckBox("BUS4")
        self.bus_offtime = QFillBox("OFF Time [sec]", 10)
        self.bus_ontime = QFillBox("ON Time [sec]", 10)
        bus_auto_start = QPushButton("START")
        bus_auto_stop = QPushButton("STOP")
        bus_auto_start.pressed.connect(lambda x=True: self.toggleAutoToggle(x))
        bus_auto_stop.pressed.connect(lambda x=False: self.toggleAutoToggle(x))
        bus_toggle_autoLayout = QGridLayout()
        bus_toggle_autoLayout.addWidget(self.bus_offtime,0,2,1,2)
        bus_toggle_autoLayout.addWidget(self.bus_ontime,0,0,1,2)
        bus_toggle_autoLayout.addWidget(bus_auto_start,1,0,1,2)
        bus_toggle_autoLayout.addWidget(bus_auto_stop,1,2,1,2)
        bus_toggle_autoLayout.addWidget(self.bus_1_toggle_auto,2,0,1,1)
        bus_toggle_autoLayout.addWidget(self.bus_2_toggle_auto,2,1,1,1)
        bus_toggle_autoLayout.addWidget(self.bus_3_toggle_auto,2,2,1,1)
        bus_toggle_autoLayout.addWidget(self.bus_4_toggle_auto,2,3,1,1)
        bus_toggle_autoWidget = QWidget()
        bus_toggle_autoWidget.setLayout(bus_toggle_autoLayout)
        busControlAutoLayout.addWidget(bus_toggle_autoWidget)

        layout = QVBoxLayout()
        layout.addWidget(reconnectButton)
        layout.addWidget(self.comportSelect)
        layout.addWidget(comportButton)
        layout.addWidget(QHLine())
        layout.addWidget(telemetryWidget)
        layout.addWidget(QHLine())
        layout.addWidget(busControlWidget)
        layout.addWidget(QHLine())
        layout.addWidget(busControlAutoWidget)
        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

    def toggleAutoToggle(self, state):
        targetList = []
        if self.bus_1_toggle_auto.isChecked():
            targetList += [1]
        if self.bus_2_toggle_auto.isChecked():
            targetList += [2]
        if self.bus_3_toggle_auto.isChecked():
            targetList += [3]
        if self.bus_4_toggle_auto.isChecked():
            targetList += [4]
        self.cmdHandler.toggleAutoToggle(state, targetList, int(self.bus_ontime.text.text()), int(self.bus_offtime.text.text()))

    def reconnectEGSE(self):
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