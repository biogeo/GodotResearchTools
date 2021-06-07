import godot
from godot import exposed, export, signal
#from godot import *

import pylink
import time
import math

SPECIAL_KEYS = {
	'escape': 27,
	'return': 13,
	'backspace': 8
	}

MODE_CALIBRATION = pylink.IN_SETUP_MODE | pylink.IN_TARGET_MODE

def generate_arbitrary_edf_filename():
	"""
	Eyelink still has an 8.3 DOS-based restriction on its EDF file names, which
	makes avoiding name collisions trickier than it should be. One solution is
	to just generate completely arbitrary file names based on the current time,
	which makes it almost impossible for names to collide and data to be
	overwritten. This does that by just base36-encoding the current time.
	"""
	alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	t = int(time.time())
	s = ''
	while t != 0:
		t,i = divmod(t, len(alphabet))
		s = alphabet[i] + s
	return s[-8:]

mode_bits = {
	pylink.IN_IDLE_MODE: 'mode_idle',
	pylink.IN_SETUP_MODE: 'mode_setup',
	pylink.IN_RECORD_MODE: 'mode_record',
	pylink.IN_TARGET_MODE: 'mode_target',
	pylink.IN_DRIFTCORR_MODE: 'mode_drift',
	pylink.IN_IMAGE_MODE: 'mode_image',
	}

@exposed
class Eyelink(godot.Node):

	# Read-only properties
	@export(str)
	@property
	def ip_address(self):
		return self._ip_address

	@export(str)
	@property
	def edf_filename(self):
		return self._edf_filename

	@export(str)
	@property
	def calibration_type(self):
		return self._calibration_type

	@export(godot.Vector2)
	@property
	def latest_sample(self):
		return godot.Vector2(*self._latest_sample)

	@export(godot.Vector2)
	@property
	def display_size(self):
		self._el.readRequest('screen_phys_coords')
		msg = self._el.readReply()
		if msg:
			items = msg.split(' ')
			items = [float(item) for item in items]
			return godot.Vector2(
				items[2] - items[0],
				items[3] - items[1],
				)
		else:
			return godot.Vector2(math.nan, math.nan)
	@display_size.setter
	def display_size(self, value):
		self._el.sendCommand(
			'screen_phys_coords = {} {} {} {}'.format(
				-value.x/2, -value.y/2,
				value.x/2, value.y/2
				)
			)

	@export(float)
	@property
	def display_distance(self):
		self._el.readRequest('screen_distance')
		msg = self._el.readReply()
		if msg:
			return float(msg)
		else:
			return math.nan
	@display_distance.setter
	def display_distance(self, value):
		self._el.sendCommand('screen_distance = {}'.format(value))

	# Parameters
	#ip_address = export(str, default='100.1.1.1')
	#calibration_type = export(str, default='HV9')
	#edf_filename = export(str, default='')

	# Signals
	connected = signal()
	disconnected = signal()
	enter_mode_idle = signal()
	exit_mode_idle = signal()
	enter_mode_setup = signal()
	exit_mode_setup = signal()
	enter_mode_record = signal()
	exit_mode_record = signal()
	enter_mode_target = signal()
	exit_mode_target = signal()
	enter_mode_drift = signal()
	exit_mode_drift = signal()
	enter_mode_image = signal()
	exit_mode_image = signal()

	# Private data
	_el = None
	_ip_address = "100.1.1.1"
	_edf_filename = ""
	_calibration_type = "HV9"
	_known_mode = 0
	_expected_mode = 0
	_latest_sample = (math.nan, math.nan)

	def _process(self, delta):
		"""
		Regular polling of the eye tracker when needed.
		"""
		if self._known_mode != self._expected_mode:
			new_mode = self._el.getCurrentMode()
			modes_entered = new_mode & ~self._known_mode
			modes_exited = self._known_mode & ~new_mode
			self._known_mode = new_mode

			if ( (modes_entered & pylink.IN_SETUP_MODE) and
					(self._expected_mode & pylink.IN_TARGET_MODE)
					):
				# We are switching to calibration mode, and have just
				# successfully entered setup mode on the way there
				self._el.sendKeybutton(ord('c'), 0, pylink.KB_PRESS)

			for flag, mode in mode_bits.items():
				if flag & modes_exited:
					self.call('emit_signal', 'exit_' + mode)
				if flag & modes_entered:
					self.call('emit_signal', 'enter_' + mode)

		if self._known_mode & pylink.IN_RECORD_MODE:
			# Update the tracker position while recording
			sample = self._el.getNewestSample()
			if sample is None:
				# No sample was available
				self._latest_sample = (math.nan, math.nan)
			else:
				if sample.isRightSample():
					self._latest_sample = sample.getRightEye().getGaze()
				else if sample.isLeftSample():
					self._latest_sample = sample.getLeftEye().getGaze()
				else:
					self._latest_sample = (math.nan, math.nan)

	def open(self, ip_address="100.1.1.1", edf_filename=""):
		self._ip_address = ip_address
		if edf_filename:
			self._edf_filename = edf_filename
		else:
			self._edf_filename = generate_arbitrary_edf_filename()
		self._el = pylink.EyeLink(str(self._ip_address))
		self._el.openDataFile(str(self._edf_filename))
		self._known_mode = self._el.getCurrentMode()
		self._expected_mode = self._known_mode
		self.set_screen_dimensions()
		self.call('emit_signal', 'connected')
		self.get_tree().connect('screen_resized', self, 'set_screen_dimensions')

	def is_open(self):
		return self._el is not None and self._el.isConnected()

	def close(self):
		if not self.is_open():
			return
		self._el.close()
		self.call('emit_signal', 'disconnected')
		tree = self.get_tree()
		if tree.is_connected('screen_resized', self, 'set_screen_dimensions'):
			tree.disconnect('screen_resized', self, 'set_screen_dimensions')

	def set_screen_dimensions(self):
		if not self.is_open():
			return
		window_pos = godot.OS.get_window_position()
		window_size = godot.OS.get_window_size()

		pixel_coords_message = (
			"0 0 {} {}".format(window_size.x-1, window_size.y-1) )

		self._el.sendCommand("screen_pixel_coords = " + pixel_coords_message)
		self._el.sendMessage("DISPLAY_COORDS " + pixel_coords_message)

	def enter_setup(self):
		if not self.is_open():
			return
		self._el.startSetup()
		self._expected_mode = pylink.IN_SETUP_MODE

	def enter_calibration(self, calibration_type="HV9"):
		if not self.is_open():
			return
		if self._known_mode & pylink.IN_SETUP_MODE:
			# We are already in setup mode, just need to change to calibration
			self._el.sendKeybutton(ord('c'), 0, pylink.KB_PRESS)
			self._expected_mode |= pylink.IN_TARGET_MODE
		else:
			# We are not yet in setup mode, so we need to go there first
			self._el.startSetup()
			self._expected_mode = MODE_CALIBRATION
		self._calibration_type = calibration_type

	def cancel_calibration(self):
		if (self.is_open() and self._known_mode == MODE_CALIBRATION):
			self._el.sendKeybutton(SPECIAL_KEYS['escape'], 0, pylink.KB_PRESS)

	def accept_cal_target(self):
		if (self.is_open() and self._known_mode == MODE_CALIBRATION):
			self._el.sendKeybutton(SPECIAL_KEYS['return'], 0, pylink.KB_PRESS)

	def previous_cal_target(self):
		if (self.is_open() and self._known_mode == MODE_CALIBRATION):
			self._el.sendKeybutton(SPECIAL_KEYS['backspace'], 0, pylink.KB_PRESS)

	def get_cal_target_position(self):
		if (self.is_open() and self._known_mode & pylink.IN_TARGET_MODE):
			return godot.Vector2(*self._el.getTargetPositionAndState()[1:3])

	def start_recording(self):
		if self.is_open():
			self._el.startRecording(1,1,1,1)
			self._expected_mode = pylink.IN_RECORD_MODE

	def stop_recording(self):
		if self.is_open():
			self._el.stopRecording()
			self._expected_mode = pylink.IN_IDLE_MODE

	def get_tracker_time_offset(self):
		if self.is_open():
			return self._el.trackerTime() - godot.OS.get_ticks_msec()
		else:
			return math.nan

	def mark_sync_event(self):
		if self.is_open():
			self._el.sendMessage(
				'DISPLAYCLOCK {}'.format(godot.OS.get_ticks_msec())
				)

	def mark_trial_start(self, trialID):
		if self.is_open():
			self._el.sendMessage('TRIALID {}'.format(trialID))

	def mark_trial_end(self):
		if self.is_open():
			self._el.sendMessage('TRIAL OK')
