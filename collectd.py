__author__ = 'denislavrov'

from cor.api import Message, CORModule
import threading
import time
import socket
import select
import sys

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
			for dp in datain.split("\n"):
				if ("found" not in dp) and dp is not "":
					(tstamp, space, identifier) = dp.partition(" ")
					self.s.sendall(("GETVAL " + identifier + "\n").encode("ASCII"))
					values = recvall(self.s).decode("UTF-8")
					lines = values.split("\n")
					vals = {}
					for val in lines:
						if ("found" not in val) and val is not "":
							(n, s, d) = val.partition("=")
							vals[n] = d
					stype = identifier.partition("/")[2]
					if stype not in self.pvals or self.pvals[stype] != tstamp:
						self.pvals[stype] = tstamp
						payload = {"type": stype, "timestamp": tstamp}
						payload.update(vals)
						self.messageout(Message("SENSOR_READING", payload))

	def __init__(self, collectd_socket="/var/run/collectd-unixsock", period=1, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.period = period
		self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			self.s.connect(collectd_socket)
		except FileNotFoundError:
			print("Could not connect to " + collectd_socket + " trying again.", file=sys.stderr)
			time.sleep(3)
			self.s.connect(collectd_socket)
		self.t = threading.Thread(target=self.check)
		self.t.start()
		self.pvals = {}
		self.add_topics({"SENSOR_FORCE_CHECK": self.force_check})
