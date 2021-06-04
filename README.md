# EyelinkTools

Tools for interfacing a Godot project with the SR Research EyeLink gaze
trackers. (This project is not affiliated with SR Research in any way.) Godot is
a promising platform for behavioral research, leveraging the advantages of a
modern game engine to remove a lot of the hard work of programming a complex
virtual environment, leaving the researcher free to focus on task design and
scientific questions. By allowing a Godot project to communicate with a high
quality research-grade gaze tracking system like EyeLink, the door is opened to
a much broader range of questions in cognitive and behavioral science.

Note: this project is currently an early work-in-progress and may not function
correctly or at all! Use at your own risk.

## Installing EyelinkTools

EyelinkTools must be installed into each Godot project that will use it.

1. Install the `godot-python` plugin for your project. Using the Godot Asset
    Library is recommended for a quick and easy installation.
2. Install the `Pylink` Python library from SR Research and its dependencies.
    SR Research keeps their proprietary SDK, including Pylink, fairly restricted
    so unfortunately it cannot be redistributed here. Make sure that the version
    of Pylink matches the Python version bundled with godot-python. The versions
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

## Using EyelinkTools

The core functionality of EyelinkTools is provided by the `Eyelink.py` AutoLoad
singleton script. Any GDScript or Python script can access Eyelink. In Godot
3.3, this can be accessed effectively as a global within GDScript; simply refer
to `Eyelink`. In older versions of Godot, you may need to call

`Eyelink = get_node("/root/Eyelink")`

within any scope requiring access to Eyelink. Within Python this still seems to
be required; the godot-python readme suggests that an AutoLoad like Eyelink
should be available directly within the `godot` module, but that doesn't seem to
work for me. Calling `self.get_node("/root/Eyelink")` should work.
