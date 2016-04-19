import datetime

from cor.api import CORModule
from .sensor_pb2 import SensorReading
import threading
import time
import socket
import sys

__author__ = 'denislavrov'


def recvall(sock):
	data = b""
	while True:
		time.sleep(0.005)
		part = sock.recv(4096)
		data += part
		if len(part) < 4096:
			break
	return data


class Collectd(CORModule):
	def force_check(self, message):
		if "collectd" in message.payload["sensors"]:
			self.check()

	def check(self):
		while True:
			time.sleep(self.period)
			self.s.sendall("LISTVAL\n".encode("ASCII"))
			datain = recvall(self.s).decode("UTF-8")
			vals_to_send = {}
			for dp in datain.split("\n"):
				if ("found" not in dp) and dp is not "":
					(tstamp, space, identifier) = dp.partition(" ")
					self.s.sendall(("GETVAL " + identifier + "\n").encode("ASCII"))
					values = recvall(self.s).decode("UTF-8")
					lines = values.split("\n")
					stype = identifier.partition("/")[2]
					for val in lines:
						if ("found" not in val) and val is not "":
							(n, s, d) = val.partition("=")
							vals_to_send[stype+"/"+n] = float(d)
			reading = SensorReading()
			reading.location = self.location
			reading.timestamp = int(time.time())
			reading.values.update(vals_to_send)
			self.messageout(reading)

	def __init__(self, location="UNKNOWN", collectd_socket="/var/run/collectd-unixsock", period=1, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.period = period
		self.location = location
		self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			self.s.connect(collectd_socket)
		except FileNotFoundError:
			print("Could not connect to " + collectd_socket + " trying again.", file=sys.stderr)
			time.sleep(3)
			self.s.connect(collectd_socket)
		self.t = threading.Thread(target=self.check)
		self.t.start()
