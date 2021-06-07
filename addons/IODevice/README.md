# IODevice

A tool for interacting with a custom Arduino-based digital I/O device, used to
control a variety of research hardware. The Arduino project is available as
[gk_util](https://github.com/platt-labs/arduino_gkutil).

## Installation

1. This depends upon `PythonScript`: install this plugin using the Godot Asset
    Library (or your preferred method).
2. Install the Python `pyserial` module. From the Python executable installed
    by `PythonScript` (in your project's addons folder), run

```
$ python -m pip install pyserial
```

3. Install this plugin, specifically the `addons/IODevice/` directory, into your
    project.

## Usage

The script `IODevice.py` provides an example of using the device to trigger a
reward-delivery system. This can be customized as needed.
