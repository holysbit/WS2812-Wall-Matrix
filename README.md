# RGB Matrix
 Large, wallmounted matrix display, with library functionality
![IMG_5753](https://github.com/user-attachments/assets/8de73d37-a69d-48cd-8918-5818aea53cc6)

This is a fully homemade LED display matrix. It features a 7x55 array of addressable WS2818 LEDs.

The LEDs are arranged in a snaking pattern, with a raspberry pi mounted on the back.

Programmatically, the matrix operates a loop of widgets, where each widget is essentially its own applet.

In between widgets there is a fun widget that runs and selects a random, fun, animation to display.

The display is really bright, so there is a schedule so the display is inactive at night. There is a twilight mode that runs between normal and off, that displays a simple red clock.

It also interacts with the NOAA API so it can display weather alerts for a region as a widget.

The files:
- matrix.py:  the matrix library I made. Can do text, symbols, animations, and basic graphics
- matrixDisplayBoard.py:   the main program code, top level. Set the display schedule and init everything
- widgets.py:  where all the widgets live, herer they run in a loop for stuff like weather, stocks, time, etc
- color.py: and simpletime.py: simple glue libraries
- font.py:   contains the whole 5x7 font, including special custom symbols.
