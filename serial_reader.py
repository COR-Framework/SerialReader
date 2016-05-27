import datetime

from cor.api import CORModule
from sensor_pb2 import SensorReading
import threading
import time
import socket
import sys
import serial

__author__ = 'denislavrov'

class SerialReader(CORModule):
	def force_check(self, message):
		if "collectd" in message.payload["sensors"]:
			self.check()

	def check(self):
		with serial.Serial(self.serial_port) as ser:
			count = 0
			ser.readline() # ignore the first line, its a lie
			while True:
				line = ser.readline().decode("ascii").strip()
				try:
					temp = float(line)
				except Exception:
					print("Bad line: ", line)
					continue
				if count % 10 == 0:
					reading = SensorReading()
					reading.location = self.location
					reading.timestamp = int(time.time())
					vals = {"temperature":temp}
					reading.values.update(vals)
					self.messageout(reading)
				count += 1

	def __init__(self, location="UNKNOWN", serial_port="/dev/cu.usbmodem1421", *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.location = location
		self.serial_port = serial_port
		self.t = threading.Thread(target=self.check)
		self.t.start()
