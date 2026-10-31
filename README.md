Python code to define signal logic on a model railroad.

#Summary

Details on project here:
https://vasonabranch.blogspot.com/2024/02/big-changes-at-signal-gulch.html

This code implements a simple model railroad signal controller.
It's intended to run on a Raspberry Pi with I2C-connected I/O pins to handle
inputs from sensors on the layout and outputs to LEDs in signals on the
layout.

Goals for this implementation:
* Avoid needing a PC to run signals.
* Run on a Raspberry Pi for easier debugging compared with Arduino or
hardcoded signals.
* Easy description and changes to signals.
* Programmed in interpreted language 

#Sample Layout

The built-in configuration is for signals on part of the Vasona Branch,
https://www.vasonabranch.com/railroad/vasona.html

The signals here represent the signaling along the Southern Pacific's
Los Gatos - Santa Cruz branch.  The actual signals here were automatic
block signals (ABS).  ABS signals only show occupancy, indicating whether another train is present (or if a switch is set against the train).  ABS does
not show whether the train is permitted to go; permission on this branch
came from telegraphed train orders.

#Implementation

The logic here was inspired by the early 2000's Team Digital SIC24 signal
interface controller boards.  These used a small microcontroller to
follow a set of signal rules programmed via a DCC programmer to set a bunch
of configuration values.  Rules weren't visible after the programming was done.
When the signal went wonky, all we could do was reprogram all the
configuration variables for the board.

The general logic idea (each output coming from a boolean logic statement
about inputs and outputs) came directly from the SIC24 programming.

The Logic class allows defining the value each output should
have based on inputs and other outputs.

Inputs and outputs are read and written via PortMapper class.

#Known Issues
Circular dependencies in outputs are handled by checking the current output
state at the time of evaluating the logic, and re-evaluating on every poll.
This can allow flashing lights to be done.
