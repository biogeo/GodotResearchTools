# EyelinkTools

Tools for interfacing a Godot project with the SR Research EyeLink gaze
trackers. (This project is not affiliated with SR Research in any way.) By
allowing a Godot project to communicate with a high quality research-grade gaze
tracking system like EyeLink, the door is opened to a much broader range of
questions in cognitive and behavioral science.

Note: this project is currently an early work-in-progress and may not function
correctly or at all! Also, it is designed entirely with cognitive/behavioral
experiments in mind, and its performance for low-level visual or oculomotor
studies is probably inadequate. Use at your own risk.

## Installation

EyelinkTools must be installed into each Godot project that will use it.

1. Install the `PythonScript` plugin for your project. Using the Godot Asset
    Library is recommended for a quick and easy installation.
2. Install the `Pylink` Python library from SR Research and its dependencies.
    SR Research keeps their proprietary SDK, including Pylink, fairly restricted
    so unfortunately it cannot be redistributed here. Make sure that the version
    of Pylink matches the Python version bundled with PythonScript. The versions
    made available by SR Research within their support forum may lag behind
    the latest Python version by several releases, but if asked nicely they may
    be willing to provide you with a more up-to-date version of the library via
    a private download.
3. Install this plugin, specifically the `addons/EyelinkTools/` directory, into
    your project.
4. Add the file `res://addons/EyelinkTools/Eyelink.py` as an AutoLoad script.
    1. Within the Godot editor, open the menu "Project > Project Settings..."
    2. Select the "AutoLoad" tab
    3. In "Path" enter `res://addons/EyelinkTools/Eyelink.py`, and for "Node
        name" enter `Eyelink`
    4. Click "Add", then close the project settings window

## Usage

### The Eyelink singleton

The core functionality of EyelinkTools is provided by the `Eyelink.py` AutoLoad
singleton script. Any GDScript or Python script can access `Eyelink`. In Godot
3.3, this can be accessed effectively as a global within GDScript; simply refer
to `Eyelink`. In older versions of Godot, you may need to call
`Eyelink = get_node("/root/Eyelink")` within any scope requiring access to
Eyelink. Within Python this still seems to be required; the `PythonScript`
readme suggests that an AutoLoad like `Eyelink` should be available directly
within the `godot` module, but that doesn't seem to work for me. In Python,
calling `self.get_node("/root/Eyelink")` should work. In any case, the `Eyelink`
singleton can be interacted with using its properties, methods, and signals.

#### Properties

##### `ip_address : str` (read-only)
The IPv4 address of the EyeLink Host PC.

##### `edf_filename : str` (read-only)
##### `calibration_type : str` (read-only)
##### `latest_sample : Vector2` (read-only)
The current gaze position in screen (x,y) coordinates, updated every `_process`
step while the tracker is in Recording Mode.

##### `display_size : Vector2`
The size of the display screen in centimeters. May be configured from Godot or
in the EyeLink configuration files. Along with `screen_distance`, this must be
set accurately if using the built-in functionality of EyeLink to convert screen
pixels to degrees of visual arc or to detect saccades.
##### `display_distance : float`
The distance between the subject and the display screen in centimeters.

#### Methods

##### `open(ip_address="100.1.1.1", [edf_filename]) -> void`
Open the TCP/IP connection to the EyeLink tracker. If not supplied,
`edf_filename` defaults to an arbitrary string generated based on the current
time, to avoid filename collisions.

##### `close() -> void`
##### `set_screen_dimensions() -> void`
Informs the EyeLink Host PC of the screen resolution or window size, which is
required if using EyeLink's calibration. This is done automatically when the
connection is opened and any time the screen resolution or window size (if
running in a window) changes, so this shouldn't normally need to be called.
Note however that if running in a window, `display_size` should also be adjusted
to reflect the physical dimensions of the window; this is one of many reasons
running in a window is not recommended.

##### `enter_setup()`
##### `enter_calibration(calibration_type="HV9")`
Puts EyeLink into Calibration Mode, using the specified target pattern. The
default pattern, "HV9", is a 3x3 grid of targets. For faster but less precise
calibration, use "HV5", a set of 5 points making a + shape across the screen.

##### `cancel_calibration()`
##### `accept_cal_target()`
If in Calibration Mode, tell EyeLink to accept the current calibration target.
If all targets have been accepted, will also accept the whole calibration.

##### `previous_cal_target()`
If in Calibration Mode, tell EyeLink to go back to the previous target.

##### `get_cal_target_position()`
If in Calibration Mode, returns a `Vector2` representing the (x,y) coordinate of
the current calibration target on the screen.

##### `start_recording()`
##### `stop_recording()`
##### `get_tracker_time_offset()`
Return the current difference between the EyeLink tracker clock and the Godot
clock (`OS.get_ticks_msec()`), in milliseconds.

##### `mark_sync_event()`
Write a message to the EDF data file to allow synchronizing the EyeLink and
Godot clocks. The message, which will have an EyeLink timestamp attached to it,
is `DISPLAYCLOCK nnnn`, where "nnnn" is the current value of Godot's
`OS.get_ticks_msec()`.

##### `mark_trial_start(trialID)`
Write a message to the EDF data file, as `TRIALID <trialID>`, EyeLink's
recommended standard to mark the start of a trial.

##### `mark_trial_end()`
Write the message `TRIAL OK` to the EDF file, EyeLink's recommended standard to
mark the end of a trial.

#### Signals

##### `connected`
##### `disconnected`
##### `enter_mode_*`, `exit_mode_*`
These signals are emitted when the EyeLink tracker mode changes. The valid modes
are:

* `idle`
* `setup`
* `record`
* `target`
* `drift`
* `image`

Note that these are "flags", and some modes are a conjunction of two of these.
In particular, Calibration Mode is effectively "setup" + "target", so switching
to Calibration Mode from Idle Mode will entail first a transition to Setup Mode
(and emitting `enter_mode_setup`), then the addition of target to become
Calibration Mode (and emitting `enter_mode_target`). Completing calibration will
cause both `exit_mode_setup` and `exit_mode_target` to be emitted.

### GazeTarget (inherits Node2D)

GazeTarget is a node representing a target on the screen to which the subject
can orient their gaze to trigger some action. A GazeTarget has a position and a
radius, represented in screen pixels. It has no visual presentation itself
(useful for memory-guided saccade tasks), but a visual target (e.g., a Circle2D
or a sprite) can be added as a child to achieve this effect.

#### Properties
##### `radius_pixels : float`
##### `acquisition_time : float`
If greater than zero, when gaze enters the target, begins a countdown for
`acquisition_time` seconds. During this time, if gaze leaves the target, the
countdown is canceled. If `acquisition_time` seconds elapse without gaze leaving
the target, `gaze_acquired` is emitted.

#### Methods
##### `has_gaze() -> bool`
True if and only if the current gaze focus is within the target.

#### Signals
##### `gaze_entered`
Emitted on any `_process` step in which the gaze focus transitions from outside
to inside the target area.

##### `gaze_acquired`
If `acquisition_time` is greater than zero, emitted on the first `_process` step
for which gaze focus has remained within the target for `acquisition_time`
seconds. If `acquisition_time` is not greater than zero, this signal is never
emitted.

##### `gaze_exited`
Emitted on any `_process` step in which the gaze focus transitions from inside
to outside the target area.

### Circle2D (inherits Node2D)
A simple helper node for drawing filled, monochrome circles, a commonly used
gaze target.

#### Properties
##### `radius : float`
##### `color : Color`

### Background2D (inherits Node2D)
A simple helper node for filling the background with a solid, uniform color.
#### Properties
##### `color : Color`

### CalibrationScreen (scene)
A scene that can be used to calibrate the EyeLink system. It can be used on its
own, or with a scene switcher. Allows the EyeLink calibration to be driven from
the Display PC running the Godot task, and displays targets where EyeLink
requests them.

#### Usage
CalibrationScreen requires these actions to be configured in the project's Input
Map (Project > Project Settings... > Input Map):

* `eyecal_next_step`
* `eyecal_prev_step`

These actions allow the experimenter to accept calibration targets or redo
previously accepted targets. Pressing the key associated with `eyecal_next_step`
once all the targets have been accepted confirms the calibration and exits
calibration mode. The signal `calibration_complete` is emitted when calibration
mode exits, which a scene switcher can use to close the scene.

#### Properties
##### `background_color : Color`
##### `target_color : Color`
##### `target_radius : float`

#### Signals
##### `calibration_complete`
