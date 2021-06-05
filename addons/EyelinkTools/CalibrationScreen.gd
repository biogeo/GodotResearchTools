extends Node2D


# Declare member variables here. Examples:
# var a = 2
# var b = "text"

var is_calibration_active = false

# Called when the node enters the scene tree for the first time.
func _ready():
	Eyelink.open()
	$TargetSpot.visible = false
	Eyelink.connect('enter_mode_target', self, 'on_calibration_ready')
	Eyelink.connect('exit_mode_target', self, 'on_calibration_finished')
	Eyelink.set_screen_dimensions()
	Eyelink.enter_calibration()

func on_calibration_ready():
	is_calibration_active = true

func on_calibration_finished():
	is_calibration_active = false

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
	
