from cor.api import Launcher
from serial_reader import SerialReader
from cor.comm import TCPSocketNetworkAdapter
import sys

if __name__ == "__main__":
	if len(sys.argv) < 2:
		raise Exception("Usage: python3 example_app.py (location)")
	sensor = Launcher()
	sensor.launch_module(SerialReader, network_adapter=TCPSocketNetworkAdapter(hostport="127.0.0.1:6091"), location=sys.argv[1])
	sensor.link_external("SensorReading", "192.168.3.3:6090")
