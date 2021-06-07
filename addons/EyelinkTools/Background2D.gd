tool
extends Node2D
class_name Background2D

export var color := Color(0,0,0)

func _draw():
	draw_rect(get_viewport_rect(), color)
