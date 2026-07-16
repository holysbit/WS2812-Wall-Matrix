# Eventually this class will do stuff like HSV-RGB conversion, but for now it really just stores colors into readable names
class Color:
    def __init__(self):
        # Format is (red, grn, blu)
        self.WHITE =    (255, 255, 255)
        self.BLACK =    (0,   0,   0)
        self.RED =      (255, 0,   0)
        self.GREEN =    (0,   255, 0)
        self.BLUE =     (0,   0, 255)
        self.YELLOW =   (255, 255, 0)
        self.MAGENTA =  (255, 0, 255)
        self.CYAN =     (0, 255, 255)

    # Converts a given RGB color to HSV, using a common approach found online
    def rgbToHsv(self, rgb):
        r = rgb[0] / 255.0
        g = rgb[1] / 255.0
        b = rgb[2] / 255.0

        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        h = -1
        if cmax == cmin:
            h = 0
        elif cmax == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif cmax == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        elif cmax == b:
            h = (60 * ((r - g) / diff) + 240) % 360
        
        if cmax == 0:
            s = 0
        else:
            s = (diff / cmax) * 100

        v = cmax * 100

        return (h, s, v)
    
    def HsvToRgb(self, hsv):
        # Unpack the HSV tuple
        h, s, v = hsv
        
        # Calculate the RGB values based on the formulas for HSV to RGB conversion
        if s == 0:
            # Achromatic (grey)
            r = g = b = int(v * 255)
            return r, g, b
        
        i = int(h * 6)  # Hue sector
        f = (h * 6) - i  # Factorial part of h
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        # Map i to the correct RGB sector
        i = i % 6

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        # Convert the RGB values from the range [0, 1] to [0, 255]
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        return (r, g, b)
