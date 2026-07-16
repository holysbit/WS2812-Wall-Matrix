import board
import neopixel
from font import font, symbols
import time

class LEDMatrix:
    # these color codes are used to print text, used as escape characters
    escapeColors = {
        'w': (255, 255, 255),
        'r': (255, 0, 0),
        'g': (0, 255, 0),
        'b': (0, 0, 255),
        'y': (255, 255, 0),
        'm': (255, 0, 255),
        'c': (0, 255, 255)
    }

    """
    This class assumes the grid is physically constructed like the following:
        LED     0   1   2   3   4   5
                11  10  9   8   7   6
                12  13  14  15  16  17 ...  serpentine pattern

    As a display matrix, the pixels are arranged like the following:
        Col 0   1   2   3   ...
    Row
    0       00  01  02  03
    1       10  11  12  13
    2       20  21  22  23
    3       30  31  32  33
    ...


    There are two ways to use this class, string or buffer functions

    String functions operate the matrix directly, and offer a few different ways to print text
        with some limited symbol support through the use of escape characters 0-9.
        Colors can be changed by using escape codes from escapeColors.

    Buffer functions are more for graphical use, and operate on an internal buffer that is
        some multiple of the size of  the matrix. The functions allow for drawing small bitmaps
        or custom symbols, and must be transferred to the matrix when they need to be displayed
    
        To save memory when not needed, you will specify if the buffer should exist during
        the instantiation of this class, that way its not always generating, taking up
        memory. To prevent unintended behavior, all buffer functions will check to see
        if the buffer is enabled, and wont do anything but return -1 if not.
    """
    def __init__(self, dataPin, rows, cols, bufferEnabled = True):
        self.dataPin = dataPin      # physical pin on the GPIO to talk to the LEDs, typ. D18
        self.rows = rows
        self.cols = cols
        self.nPix = rows * cols
        self.order = neopixel.GRB   # function of the neopixel library
        self.brightness = 0.045     # default brightness is 0.045

        self.speed = 0.03           # time in seconds between animation frames
        self.delay = 0.5            # time in seconds to hold after finishing an animation

        self.matrix = neopixel.NeoPixel(
            self.dataPin, self.nPix, brightness = self.brightness, auto_write = False,
        pixel_order = self.order
        )

        if bufferEnabled:
            self.bufferEnabled = True
            BUFFER_SCALE_ROW = 7    # how much larger should the buffer be compared to the matrix
            BUFFER_SCALE_COL = 2
            self.bufferRows = (self.rows * BUFFER_SCALE_ROW) + 2    # add two to maintain a 1 element border around the buffer
            self.bufferCols = (self.cols * BUFFER_SCALE_COL) + 2
            # Buffer format is (r, g, b, brightnessMod) where brightness mod can dim the entire color
            self.buffer = [[(0, 0, 0, 0) for _ in range(self.bufferRows)] for _ in range(self.bufferCols)]
        else:
            self.bufferEnabled = False
            self.bufferRows = -1
            self.bufferCols = -1
            self.buffer = []
    
    # Getter and setter for brightness from 0.0 to 1.0
    def setBrightness(self, brightness):
        self.brightness = brightness
        self.matrix.brightness = self.brightness
    
    # Getter and setter for speed
    # Time between animation frames in seconds
    def setSpeed(self, speed):
        self.speed = speed

    # Getter and setter for delay
    # Hold time after the animation in seconds
    def setDelay(self, delay):
        self.delay = delay

    
    def clearDisplay(self):
        self.matrix.fill((0,0,0))
        self.matrix.show()


    """
    @brief:     Draws a pixel at any location on the matrix, assuming a serptentine design
    @note:      This really converts the row/col to a linear position along the strip
    @note:      Does not update the matrix, call matrix.show() after this
    @param:     row         The row from zero to self.rows
    @param:     col         The col of the pixel from zero to self.cols
    @param:     color       The color represented as (RED, GRN, BLU)
    @retval:    boolean     True if the pixel is within the matrix, false otherwise
    """
    def matrixDrawPixel(self, row, col, color, brightnessMod = 1.0):
        # Some functions require drawing pixels outside the visible area, so make sure
        # we dont try to actually color an area thats off the matrix
        if (row <= (self.rows-1) and row >= 0 and col <= (self.cols-1) and col >= 0):
            # For even rows, the  math is simple
            if (row % 2 == 0):
                position = (row * self.cols) + (col)
            else:
                # odd rows need to have nCol - (2 * col) added
                position = (row * self.cols) + (col - 1)  + (self.cols - (2 * col))

            # We already know this position is within the matrix, so color it after applying the brightness modifier
            drawColor = tuple(int(x * brightnessMod) for x in color)
            self.matrix[position] = drawColor
            return True
        else:
            return False


    """
    @brief:     Uses drawPixel to render a string of characters on the matrix
    @note:      Drawing to buffer will not update the matrix, use bufferWindowToMatrix to see changes
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     show        Default True, whether or not to update the matrix at the end
    @param:     toBuffer    Default False, whether to draw to the physical matrix or its display buffer
    @retval:    None
    """
    def stringPrint(self, string, color, startCol = 0, startRow = 0, show = True):
        # These are shadows of the params, because they need to change
        drawCol = startCol
        drawColor = color

        if show == True:
            self.matrix.fill((0,0,0))

        # We will iterate through each character of the string
        index = 0
        while index <= len(string) - 1:
            char = string[index]
            
            # Do we need to process an escape character?
            if char == '\\':
                nextChar = string[index + 1]
                if nextChar.isnumeric():
                    # Pick a symbol from the symbol dictionary
                    drawData = symbols[int(nextChar)]
                    for row in range(7):
                        for col in range(7):
                            if (drawData[row][col] == 1):
                                self.matrixDrawPixel(startRow + row, drawCol + col, drawColor)
                    drawCol += 7
                    None

                elif nextChar in self.escapeColors:  # here we know if we need to change the color
                    drawColor = self.escapeColors[nextChar]

                index += 1  # we need to advance past the color char, so add one to index

            else:   # Not an escape char, so just draw the character
                # The character data is a 7x7 matrix of binary, 
                # telling which pixels need to be lit to make the character
                charData = font[char]
                for row in range(7):
                    for col in range(7):
                        if (charData[row][col] == 1):
                            self.matrixDrawPixel(startRow + row, drawCol + col, drawColor)
                drawCol += 7

            index += 1
        
        if show == True:
            self.matrix.show()


    """
    @brief:     Displays an entire string, scrolling the text left until the whole string shows
    @note:      A lower lenModifier results in the text scrolling further left before stopping
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @param:     lenModifier Default 10, adjustment to make sure longer strings scroll entirely off screen
    @retval:    None
    """
    def stringExitLeft(self, string, color, startCol, startRow = 0, speed = None, delay = None, lenModifier = 10):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay

        col = startCol

        # we need the amount of characters to draw, subtracting the escape characters
        lenPix = (len(string) * 7) - (string.count("\\") * lenModifier)  

        # Essentially we just move the startCol leftwards, until the entire string has scrolled across the matrix
        while col >= (-1 * lenPix):
            self.stringPrint(string, color, col, startRow)
            time.sleep(speed)
            col -= 1
        time.sleep(delay)


    """
    @brief:     Scrolls text vertically, from bottom to top, stopping when the string is displayed
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     endRow      Default 0, The row that the text will stop at, as it scrolls up
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @retval:    None
    """ 
    def stringEnterBottom(self, string, color, startCol = 0, endRow = 0, speed = None, delay = None):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay

        row = 6
        # move the string up, row by row, until we get to endRow (defualt zero)
        # but only if endRow is between 0 and 6 inclusive
        if endRow <= 6 and endRow >= 0:
            while row >= endRow:
                self.stringPrint(string, color, startCol, row)
                row -= 1
                time.sleep(speed)
            time.sleep(delay)
    

    """
    @brief:     Displays a string, but scrolls it vertically until its off screen
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @retval:    None
    """
    def stringExitTop(self, string, color, startCol = 0, startRow = 0, speed = None, delay = None):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay

        while startRow >= -7:
            self.stringPrint(string, color, startCol, startRow)
            startRow -= 1
            time.sleep(speed)
        time.sleep(delay)


    """
    @brief:     Scrolls a string up, holds, then scrolls up until its off screen
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @param:     displayTime Default 4, Time in seconds to show the string before scrolling it away
    @retval:    None
    """
    def stringEnterBottomExitTop(self, string, color, startCol = 0, startRow = 0, speed = None, delay = None, displayTime = 4):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay
        
        self.stringEnterBottom(string, color, startCol, startRow, speed, delay)
        time.sleep(displayTime)
        self.stringExitTop(string, color, startCol, startRow, speed, delay)
        time.sleep(delay)


    """
    @brief:     Scrolls a string up, holds, then scrolls left until its off screen
    @note:      A lower lenModifier results in the text scrolling further left before stopping
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @param:     displayTime Default 1, Time in seconds to show the string before scrolling it away
    @param:     lenModifier Default 10, adjustment to make sure longer strings scroll entirely off screen
    @retval:    None
    """
    def stringEnterBottomExitLeft(self, string, color, startCol = 0, startRow = 0, speed = None, delay = None, displayTime = 1, lenModifier = 10):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay
        
        self.stringEnterBottom(string, color, startCol, startRow, speed, delay)
        time.sleep(displayTime)
        self.stringExitLeft(string, color, startCol, startRow, speed, delay, lenModifier)
        time.sleep(delay)


    """
    @brief:     Scrolls a string left, holds, then scrolls left until its off screen
    @param:     string      The string to be rendered on the display
    @param:     color       The color as (RED,GRN,BLU)
    @param:     startCol    Default 0, The column to start the string at
    @param:     startRow    Default 0, the row to print the text on
    @param:     speed       Time in seconds between animation frames
    @param:     delay       Time in seconds to hold after the animation finishes
    @param:     displayTime Default 2, Time in seconds to show the string before scrolling it away
    @retval:    None
    """
    def stringEnterRightExitLeft(self, string, color, startCol = None, startRow = 0, speed = None, delay = None, displayTime = 2):
        # Handle default parameters according to the class defaults
        if speed == None:
            speed = self.speed
        if delay == None:
            delay = self.delay
        if startCol == None:
            startCol = self.cols
        
        lenPix = (len(string) * 7) - (string.count("\\") * 14)

        # start from the right, scroll in, and stop at column 0
        while startCol >= 0:
            self.stringPrint(string, color, startCol, startRow)
            startCol -= 1
            time.sleep(speed)
        time.sleep(displayTime)
        # now scroll until the string is off screen
        while (startCol >= (-1 * lenPix)):
            self.stringPrint(string, color, startCol, startRow)
            startCol -= 1
            time.sleep(speed)         

        time.sleep(delay)





    ######################################
    ##  String functions ^^^            ##
    ######################################
    ##  Buffer functions vvv            ##
    ######################################








    # Draws a specific pixel in the buffer
    def bufferDrawPixel(self, row, col, color, brightnessMod = 1.0):
        if self.bufferEnabled:
            if (row <= (self.bufferRows-1) and row >= 0 and col <= (self.bufferCols-1) and col >= 0):
                #print(f"Write to Buffer[{row}][{col}]")
                self.buffer[row][col] = (color + (brightnessMod,))
                return True
            else:
                return False
        else:
            return -1

    # clears out the buffer
    def clearBuffer(self):
        if (self.bufferEnabled):
            self.buffer = [[(0, 0, 0, 0) for _ in range(self.bufferCols)] for _ in range(self.bufferRows)]
        else:
            return -1
    
    # fills the buffer with one color
    def fillBuffer(self, color, brightnessMod = 1.0):
        if (self.bufferEnabled):
            self.buffer = [[(color + (brightnessMod,)) for _ in range(self.bufferCols)] for _ in range(self.bufferRows)]
        else:
            return -1

    # diagnostic tool, prints buffer to a txt file to make it easy to view
    def _printBuffer(self):
        if self.bufferEnabled:
            outputFile = open("buffer.txt", "a")

            rows = len(self.buffer)
            cols = len(self.buffer[0]) if rows > 0 else 0
            outputFile.write("\n\nBuffer has " + str(rows) + " rows and " + str(cols) + " cols\n")

            for row in range(self.bufferRows):
                disp = ""
                for col in range(self.bufferCols):
                    #print(self.buffer[row])
                    if self.buffer[row][col] != (0, 0, 0, 0):
                        disp += "X"
                    else:
                        disp += "-"
                outputFile.write(disp + "\n")
            outputFile.close()
        else:
            return -1

    # copies a window from the buffer to a position on the matrix
    # The size of the window to be copied defaults to the size of the matrix
    #   and the matrix position to copy the buffer to defaults to the top left corner (0,0)
    def bufferWindowToMatrix(self, bufferRowCol, windowSizeHW = None, matrixRowCol = (0, 0)):
        if self.bufferEnabled:
            # Handle class driven default window size
            if windowSizeHW == None:
                windowSizeHW = (self.rows, self.cols)

            for col in range(windowSizeHW[1]):
                disp = ""
                for row in range(windowSizeHW[0]):
                    #print(f"Buffer[{(row+bufferRowCol[0] + 1) % (self.bufferRows - 2)}][{(col+bufferRowCol[1] + 1) % (self.bufferCols - 2)}]")
                    color = self.buffer[(row+bufferRowCol[0] + 1) % (self.bufferRows - 2)][(col+bufferRowCol[1] + 1) % (self.bufferCols - 2)]
                    #color = self.buffer[(col+bufferRowCol[1] + 1) % (self.bufferCols - 2)][(row+bufferRowCol[0] + 1) % (self.bufferRows - 2)]
                    self.matrixDrawPixel(row + matrixRowCol[0], col + matrixRowCol[1], color[0:3], brightnessMod=color[3])
                    
            self.matrix.show()
        else:
            return -1

    # writes a string to the buffer using the included font
    def bufferStringPrint(self, string, color, startRow=0, startCol=0):
        if self.bufferEnabled:
            # These are shadows of the params, because they need to change
            drawCol = startCol
            drawColor = color

            # We will iterate through each character of the string
            index = 0
            while index <= len(string) - 1:
                char = string[index]

                # Do we need to process an escape character?
                if char == '\\':
                    nextChar = string[index + 1]
                    if nextChar.isnumeric():
                        # Pick a symbol from the symbol dictionary
                        drawData = symbols[int(nextChar)]
                        for row in range(7):
                            for col in range(7):
                                if (drawData[row][col] == 1):
                                    # The modulo is to take care of wrapping, in case the string is too big for the buffer,
                                    # though it will overwrite over itself if not used mindfully
                                    self.buffer[(startRow + row + 1) % (self.bufferRows - 2)][(drawCol + col + 1) % (self.bufferCols - 2)] = (drawColor + (0,))
                        drawCol += 7

                    elif nextChar in self.escapeColors:  # here we know if we need to change the color
                        drawColor = self.escapeColors[nextChar]

                    index += 1  # we need to advance past the color char, so add one to index

                else:   # Not an escape char, so just draw the character
                    # The character data is a 7x7 matrix of binary, 
                    # telling which pixels need to be lit to make the character
                    charData = font[char]
                    for row in range(7):
                        for col in range(7):
                            if (charData[row][col] == 1):

                                # The row and col values have 1 added to maintain a 1 pixel border around the buffer, to make scrolling look neat
                                # the -2 in the modulo is to make rollover account for that extra border space
                                self.buffer[(startRow + row + 1) % (self.bufferRows - 2)][(drawCol + col + 1) % (self.bufferCols - 2)] = (drawColor + (0,))
                    drawCol += 7

                index += 1
        else:
            return -1
    
