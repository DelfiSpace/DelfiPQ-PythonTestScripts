# DelfiPQ-PythonTestScripts
Collection of scripts in python to do functional tests

- PQ9Client.py : Python module to interact with EGSE Java application (localhost:10000)

- PQ9BusFromFile.py : Application to send a file containing PQ9 Data Frames over the Bus and log responses
- PQ9GetTelemetry.py : Application that requests Telemetry data from module and logs into a .csv
- PQ9EPSTesting.py : GUI for testing EPS. Logs Telemetry and has both manual and automatic power-bus control (requires PySide2 using 'pip install pyside2'

# Running

Type pytest --system=ADCS to run the test of the ADCS system
Type pytest --destination=ADCS test_PingService.py to run the PingService test on the ADCS board

