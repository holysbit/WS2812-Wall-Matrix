import time
import board
import neopixel
from font import font
from datetime import datetime, timezone
from time import strftime
import requests, json
import yfinance
from matrix import LEDMatrix
from simpleTime import Time
from widgets import Widget


def main():
    # Initialize the hardware, these values wont change
    dataPin = board.D18
    rows = 7
    cols = 55
    mat = LEDMatrix(dataPin, rows, cols, bufferEnabled = True)

    # Here the different behavior times can be configured
    # Time 0: Wakeup    - When the first enable the display as a red clock (no widgets)
    # Time 1: Morning   - Begin showing widgets at regular brightness
    # Time 2: Evening   - Stop widgets, return to red clock without widgets
    # Time 3: Off       - Turn off the display completely
    schedule = [Time(5, 30), Time(6, 30), Time(23, 00), Time(23, 50)]

    # Widgets have been moved to their own class and now need instantiation
    w = Widget(mat)

    w._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Program starting.")

    # This is the main program loop, to run forever
    while True:
        # Manage brightness according to time
        now = datetime.now()

        # Testing, so use schedule override
        #mat.setBrightness(0.045)
        #while True:
        #    w.widget_runLoop()


        # The schedule tells us what we need to run
        if schedule[3].compare(now) or not schedule[0].compare(now):
            # Night mode, no display, sleep for a bit
            mat.clearDisplay()
            time.sleep(120)

        elif (schedule[0].compare(now) and not schedule[1].compare(now)) or (schedule[2].compare(now) and not schedule[3].compare(now)):
            # red clock, no widgets
            mat.setBrightness(0.005)
            w.widget_NightClock()

        elif schedule[1].compare(now) and not schedule[2].compare(now):
            # full normal operation
            mat.setBrightness(0.045)
            w.widget_runLoop()

if __name__ == '__main__':
    main()