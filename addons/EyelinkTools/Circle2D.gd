tool
extends Node2D
class_name Circle2D

export var radius : float = 10
export var color : Color = Color(1.0, 1.0, 1.0)

func _draw():
	draw_circle(Vector2(0,0), radius, color)
