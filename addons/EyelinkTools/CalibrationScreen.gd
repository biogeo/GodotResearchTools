extends Node2D

signal calibration_complete

export var background_color := Color(0.25, 0.25, 0.25)
export var target_color := Color(1.0, 0.0, 0.0)
export var target_radius : float = 20

var is_calibration_active : bool = false
var hangup_when_done : bool

func _enter_tree():
	if Eyelink.is_open():
		hangup_when_done = false
	else:
		hangup_when_done = true
		Eyelink.open()

func _exit_tree():
	if hangup_when_done:
		Eyelink.close()

func _ready():
	$Background.color = background_color
	$TargetSpot.color = target_color
	$TargetSpot.radius = target_radius
	$TargetSpot.visible = false
	Eyelink.connect('enter_mode_target', self, 'on_calibration_ready')
	Eyelink.connect('exit_mode_target', self, 'on_calibration_finished')
	Eyelink.enter_calibration()

func on_calibration_ready():
	is_calibration_active = true

func on_calibration_finished():
	is_calibration_active = false
	emit_signal('calibration_complete')

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _physics_process(delta):
	if not is_calibration_active:
		return
	$TargetSpot.position = Eyelink.get_cal_target_position()
	if Input.is_action_just_pressed('eyecal_next_step'):
		if $TargetSpot.visible:
			Eyelink.accept_cal_target()
			$TargetSpot.visible = false
		else:
			$TargetSpot.visible = true
	if Input.is_action_just_pressed('eyecal_prev_step'):
		if $TargetSpot.visible:
			$TargetSpot.visible = false
		else:
			Eyelink.previous_cal_target()
			$TargetSpot.visible = false
