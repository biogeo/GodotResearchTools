tool
extends Node2D
class_name GazeTarget

export var radius_pixels : float = 10.0
export var acquisition_time : float = -1.0

signal gaze_entered
signal gaze_acquired
signal gaze_exited

var is_gaze_within : bool = false
var acquisition_armed : bool = false
var acquisition_start_time : float = 0.0

const display_color = Color(0.9, 0.0, 1.0)

func has_gaze():
    return is_gaze_within

func _draw():
    if Engine.editor_hint():
        draw_arc(Vector2(0,0), radius_pixels, 0.0, TAU, 30, display_color)

func _process():
    if Engine.editor_hint():
        return
    var gaze_distance : float = global_position.distance_to(Eyelink.latest_sample)

    if gaze_distance <= radius_pixels and not is_gaze_within:
        acquisition_start_time = OS.get_ticks_msec()
        if acquisition_time > 0:
            acquisition_armed = true
        is_gaze_within = true
        emit_signal('gaze_entered')
    elif gaze_distance > radius_pixels and is_gaze_within:
        is_gaze_within = false
        acquisition_armed = false
        emit_signal('gaze_exited')
    elif (
            acquisition_armed and
            OS.get_ticks_msec() >= acquisition_start_time+1000*acquisition_time
            ):
        acquisition_armed = false
        emit_signal('gaze_acquired')
