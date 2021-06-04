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

	# Parameters
	ip_address = export(str, default='100.1.1.1')
	calibration_type = export(str, default='HV9')

	# Signals
	edf_filename_set = signal()
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

	# Class data
	el = None
	edf_filename = None
	known_mode = 0
	expected_mode = 0

	def _ready(self):
		"""
		"""
		pass

	def _physics_process(self, delta):
		"""
		Regular polling of the eye tracker when needed.
		"""
		if self.known_mode != self.expected_mode:
			new_mode = self.el.getCurrentMode()
			modes_entered = new_mode & ~self.known_mode
			modes_exited = self.known_mode & ~new_mode
			self.known_mode = new_mode

			if ( (modes_entered & pylink.IN_SETUP_MODE) and
					(self.expected_mode & pylink.IN_TARGET_MODE)
					):
				# We are switching to calibration mode, and have just
				# successfully entered setup mode on the way there
				self.el.sendKeybutton(ord('c'), 0, pylink.KB_PRESS)

			for flag, mode in mode_bits.items():
				if flag & modes_exited:
					self.call('emit_signal', 'exit_' + mode)
				if flag & modes_entered:
					self.call('emit_signal', 'enter_' + mode)

	def open(self):
		if self.edf_filename is None:
			self.edf_filename = generate_arbitrary_edf_filename()
		self.el = pylink.EyeLink(str(self.ip_address))
		self.el.openDataFile(str(self.edf_filename))
		self.known_mode = self.el.getCurrentMode()
		self.expected_mode = self.known_mode

	def set_screen_dimensions(self, screen_size=None, screen_distance=None):
		if self.el is None or not self.el.isConnected():
			return
		window_pos = godot.OS.get_window_position()
		window_size = godot.OS.get_window_size()

		self.el.sendCommand(
			'screen_pixel_coords = {} {} {} {}'.format(
				window_pos[0], window_pos[1],
				window_size[0]-1, window_size[1]-1
				)
			)
		self.el.sendMessage(
			'DISPLAY_COORDS {} {} {} {}'.format(
				window_pos[0], window_pos[1],
				window_size[0]-1, window_size[1]-1
				)
			)

		if screen_size is not None:
			self.el.sendCommand(
				'screen_phys_coords = {} {} {} {}'.format(
					-screen_size[0]/2, -screen_size[1]/2,
					screen_size[0]/2, screen_size[1]/2
					)
				)

		if screen_distance is not None:
			self.el.sendCommand(
				'screen_distance = {}'.format(screen_distance)
				)

	def enter_setup(self):
		if self.el is None or not self.el.isConnected():
			return
		self.el.startSetup()
		self.expected_mode = pylink.IN_SETUP_MODE

	def enter_calibration(self):
		if self.el is None or not self.el.isConnected():
			return
		if self.known_mode & pylink.IN_SETUP_MODE:
			# We are already in setup mode, just need to change to calibration
			self.el.sendKeybutton(ord('c'), 0, pylink.KB_PRESS)
			self.expected_mode |= pylink.IN_TARGET_MODE
		else:
			# We are not yet in setup mode, so we need to go there first
			self.el.startSetup()
			self.expected_mode = MODE_CALIBRATION

	def cancel_calibration(self):
		if ( self.el is not None and
				self.el.isConnected() and
				self.known_mode == MODE_CALIBRATION
				):
			self.el.sendKeybutton(SPECIAL_KEYS['escape'], 0, pylink.KB_PRESS)

	def accept_cal_target(self):
		if ( self.el is not None and
				self.el.isConnected() and
				self.known_mode == MODE_CALIBRATION
				):
			self.el.sendKeybutton(SPECIAL_KEYS['return'], 0, pylink.KB_PRESS)

	def previous_cal_target(self):
		if ( self.el is not None and
				self.el.isConnected() and
				self.known_mode == MODE_CALIBRATION
				):
			self.el.sendKeybutton(SPECIAL_KEYS['backspace'], 0, pylink.KB_PRESS)

	def get_cal_target_position(self):
		if ( self.el is not None and
				self.el.isConnected() and
				self.known_mode & pylink.IN_TARGET_MODE
				):
			print(self.el.getTargetPositionAndState())
			return godot.Vector2(*self.el.getTargetPositionAndState()[1:2])

	def start_recording(self):
		if self.el is not None:
			self.el.startRecording(1,1,1,1)
			self.expected_mode = pylink.IN_RECORD_MODE

	def stop_recording(self):
		if self.el is not None:
			self.el.stopRecording()
			self.expected_mode = pylink.IN_IDLE_MODE

	def get_tracker_time_offset(self):
		if self.el is not None and self.el.isConnected():
			return self.el.trackerTime() - godot.OS.get_ticks_msec()
		else:
			return math.nan

	def mark_sync_event(self):
		if self.el is not None and self.el.isConnected():
			self.el.sendMessage(
				'DISPLAYCLOCK {}'.format(godot.OS.get_ticks_msec())
				)

	def mark_trial_start(self, trialID):
		if self.el is not None and self.el.isConnected():
			self.el.sendMessage('TRIALID {}'.format(trialID))

	def mark_trial_end(self):
		if self.el is not None and self.el.isConnected():
			self.el.sendMessage('TRIAL OK')
