from datetime import datetime

"""
This library is probably gratuitous but the behavior 
of datetime objects did not fit the way that I wanted
to schedule the operations of the RGB matrix display board.

All I needed was simple hour/minute time objects,
and the ability to import a datetime object into it.
"""

class Time:
    def __init__(self, hours=0, minutes=0):
        self.hours = hours
        self.minutes = minutes
        self.totalMinutes = (hours * 60) + minutes
    
    def setHours(self, hours):
        self.hours = hours
        self.totalMinutes = (hours * 60) + self.minutes
        return hours

    def setMinutes(self, minutes):
        self.minutes = minutes
        self.totalMinutes = (self.hours * 60) + minutes
        return minutes
    
    def setTime(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes
        self.totalMinutes = (self.hours * 60) + self.minutes
        return self.totalMinutes

    """
    @brief:     Takes the time from a datetime and sets internal data
    @note:      Total minutes is represented by (hour * 60) + minutes
    @param:     dt      Datetime object to be imported
    @retval:    Returns the total minutes of the time that was imported
    """
    def importDatetime(self, dt):
        self.minutes = dt.minutes
        self.hours = dt.minutes
        self.totalMinutes = (self.hours * 60) + self.minutes
        return self.totalMinutes
    
    """
    @brief:     Compares self with another time object
    @note:      Works with self type objects and datetime objects
    @note:      now < self: False, now > self: True
    @param:     t       Another time object to be compared
    @retval:    Returns true if self is earlier in time than t, false otherwise
    """
    def compare(self, t):
        if isinstance(t, Time):
            if (self.totalMinutes <= t.totalMinutes):
                return True
            else:
                return False
            
        elif isinstance(t, datetime):
            dtMinutes = (t.hour * 60) + t.minute
            if (self.totalMinutes <= dtMinutes):
                return True
            else:
                return False
            
        else:
            return None