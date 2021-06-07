from godot import exposed, export
from godot import *

from IODevice.EthIO import EthIO

@exposed
class IODevice(Node):
	port_name = export(str, default='/dev/ttyUSB0')
	reward_pin = export(int, default=13)
	reward_amount = export(int, default=1000)

	def open(self):
		self.device = EthIO(str(self.port_name))

	def config_output(self):
		self.device.config_output(int(self.reward_pin))

	def reward(self):
		# Temporary fix for the Arduino Uno, which seems to have a bit of a
		# delay before it can accept commands after the connection is opened
		self.device.config_output(int(self.reward_pin))
		self.device.pulse_after(int(self.reward_pin), int(self.reward_amount))
