from matrix import LEDMatrix
from datetime import datetime, timezone
from time import strftime
import time
import requests
from simpleTime import Time
import yfinance as yf
import random
import inspect
from color import Color
import math

class Widget:

    # Google Maps Distance Matrix API (for widget_TransitTime)
    last_GoogleAPI_Call = 0         # for getting transit times
    transitTime = 0                 # minutes of travel time to work, this will be what is displayed

    # Tomorrow API for Weather, conditions come in as integer strings
    last_TomorrowAPI_Call = 0       # for weather data
    weatherCodes = {
        "0": "Unknown",
        "1000": "Clear, Sunny",
        "1100": "Mostly Clear",
        "1101": "Partly Cloudy",
        "1102": "Mostly Cloudy",
        "1001": "Cloudy",
        "2000": "Fog",
        "2100": "Light Fog",
        "4000": "Drizzle",
        "4001": "Rain",
        "4200": "Light Rain",
        "4201": "Heavy Rain",
        "5000": "Snow",
        "5001": "Flurries",
        "5100": "Light Snow",
        "5101": "Heavy Snow",
        "6000": "Freezing Drizzle",
        "6001": "Freezing Rain",
        "6200": "Light Freezing Rain",
        "6201": "Heavy Freezing Rain",
        "7000": "Ice Pellets",
        "7101": "Heavy Ice Pellets",
        "7102": "Light Ice Pellets",
        "8000": "Thunderstorm"
    }
    WeatherResponseData = []

    # Yahoo finance API for stock price
    last_YahooAPI_Call = 0          # for stock price data
    ticker = None
    history = None

    # NewsAPI API for news headlines
    last_NewsAPI_Call = 0
    headlines = []
    headlineCount = 0

    # National Weather Service for alerts and weather data
    last_NWSAPI_Call = 0
    NWSResponseData = []
    NWSAPIDelay = 5

    # Storage for our sensetive data like addresses and API keys
    # Data that should not go into version control
    secrets = {}

    mat = None

    def __init__(self, matrix):
        self.mat = matrix
        self.__getsecrets()
        self.c = Color()
    
    # runs through all the widgets in series
    def widget_runLoop(self):
        self.widget_Animation()

        self.widget_Alerts()
        self.widget_CalendarClock()
        self.widget_TransitTime()

        self.widget_Animation()

        self.widget_StockPrice()
        self.widget_NewsHeadlines()
        self.widget_Weather()

        # TODO: add other widgets here
        time.sleep(4)

    # Displays time and date, fancylike
    def widget_CalendarClock(self):
        try:
            timeString = "\\w" + strftime("%I:%M:%S")
            self.mat.stringEnterBottom(timeString, self.c.RED, delay = 0)
            start = datetime.now()
            while (datetime.now() - start).total_seconds() <= 5:
                timeString = "\\w" + strftime("%I:%M:%S")
                self.mat.stringPrint(timeString, self.c.RED)
            self.mat.stringExitTop(timeString, self.c.RED, delay = 1)

            dateString = "\\w" + strftime("%m/%d/%y")
            self.mat.stringEnterBottomExitTop(dateString, self.c.RED, delay = 2, displayTime = 3)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            self.mat.stringEnterBottomExitLeft("Error in calendar clock widget.", self.c.RED, speed=0, delay=0, displayTime=0.3)
    

    # Uses the Google Maps Distance Matrix API to display the transit time (in traffic)
    # between an origin and destination
    def widget_TransitTime(self):
        try:
            # The API delay is scheduled, it should be shorter in the morning before work
            # and longer the rest of the day
            highSpeedStart = Time(7, 00)
            highSpeedEnd = Time(8, 00)
            now = datetime.now()
            if (highSpeedStart.compare(now) and not highSpeedEnd.compare(now)):
                API_DELAY = 3
            else:
                API_DELAY = 60

            # Build the request URL to get the JSON from
            origin = self.secrets["TransitOrigin"]
            destination  = self.secrets["TransitDestination"]
            APIKey = self.secrets["GoogleDistanceMatrix"]
            trafficModel = "best_guess"
            departureTime = "now"
            units = "imperial"
            requestURL = "https://maps.googleapis.com/maps/api/distancematrix/json?departure_time=" + departureTime + "&traffic_model="
            requestURL += trafficModel + "&destinations=" + destination + "&origins=" + origin + "&units=" + units + "%20&key=" + APIKey

            # first we need to know if its time to call the API
            now = int(datetime.now(timezone.utc).timestamp())
            if (now - self.last_GoogleAPI_Call > (API_DELAY * 60)):
                # We need to call the API again
                self._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Calling Google Distance Matrix API.")
                self.last_GoogleAPI_Call = now
                response = requests.get(requestURL)
                if response.status_code == 200:
                    data = response.json()
                    main = data['rows'][0]['elements'][0]['duration_in_traffic']
                    self.transitTime = int(int(main['value']) / 60)
                else:
                    self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: Google Distance Matrix API Response " + response.status_code)
            
            # Apply fancy colors to the string depending on how long it takes to get to work
            dispString = self.secrets["workplaceName"] + ": "
            if self.transitTime < 20:
                dispString += "\\g"
            elif self.transitTime < 25:
                dispString += "\\y"
            elif self.transitTime >= 30:
                dispString += "\\r"
            else:
                dispString += "\\w"
            dispString += str(self.transitTime) + "m"

            self.mat.stringEnterBottomExitTop(dispString, self.c.WHITE)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            self.mat.stringEnterBottomExitLeft("Error in transit time widget.", self.c.RED, speed=0, delay=0, displayTime=0.3)


    # Uses yfinance to show the price and history for a ticker symbol
    def widget_StockPrice(self):
        try:
            API_DELAY = 5

            tickerSymbol = 'VOO'

            # first we need to know if its time to call the API
            now = int(datetime.now(timezone.utc).timestamp())
            if (now - self.last_YahooAPI_Call > (API_DELAY * 60)):
                # We need to call the API again
                self._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Calling Yahoo Finance API.")
                self.last_YahooAPI_Call = now
                self.ticker = yf.Ticker(tickerSymbol)
                self.history = self.ticker.history(period = '5d')

            # Process the data to get the numbers
            lastClose = self.history['Close'][-1]
            previousClose = self.history['Close'][-2]
            currentPrice = self.history['Close'][0]

            difference = lastClose - previousClose
            percent = math.fabs((difference / previousClose) * 100.0)

            # Build and display the string
            dispString = "VOO:$" + str(round(currentPrice, 2)) + " Last:"
            if difference <= 0:
                dispString += "\\r\\3"  # symbol 3 is down stock arrow
            elif difference > 0:
                dispString += "\\g\\2"  # symbol 2 is up stock arrow
            dispString += str(round(percent,2)) + "%"

            self.mat.stringEnterBottomExitLeft(dispString, self.c.WHITE)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            self.mat.stringEnterBottomExitLeft("Error in stock price widget.", self.c.RED, speed=0, delay=0, displayTime=0.3)


    # Gets the weahter from the Tomorrow API
    def widget_Weather(self):
        try:
            API_DELAY = 15

            lat = self.secrets["WeatherLat"]
            long = self.secrets["WeatherLong"]
            apiKey = self.secrets["TomorrowWeather"]
            requestURL = "https://api.tomorrow.io/v4/weather/forecast?location="+lat+","+long+"&apikey="+apiKey

            now = int(datetime.now(timezone.utc).timestamp())
            if (now - self.last_TomorrowAPI_Call > (API_DELAY * 60)):
                self._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Calling Tomorrow.io Weather API.")
                self.last_TomorrowAPI_Call = now
                response = requests.get(requestURL)
                if response.status_code == 200:
                    self.WeatherResponseData = response.json()
                else:
                    self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: Tomorrow.io Weather API Response " + response.status_code)
            
            # Process self.WeatherResponseData as it has the most recent data
            hour = datetime.now().hour
            nowData = self.WeatherResponseData['timelines']['hourly'][hour]['values']
            nowConditions = str(self.weatherCodes[str(nowData['weatherCode'])])
            nowTemperature = float(nowData['temperature'])
            nowTemperatureF = str(int(nowTemperature * 1.8 + 32))

            todayData = self.WeatherResponseData['timelines']['daily'][0]['values']
            todayConditions = str(self.weatherCodes[str(todayData['weatherCodeMax'])])    #weatherCodeMax gives worst conditions of the day
            todayHigh = float(todayData['temperatureMax'])
            todayHighF = str(int(todayHigh * 1.8 + 32))
            todayLow = float(todayData['temperatureMin'])
            todayLowF = str(int(todayLow * 1.8 + 32))
            
            tomorrowData = self.WeatherResponseData['timelines']['daily'][1]['values']
            tomorrowConditions = str(self.weatherCodes[str(tomorrowData['weatherCodeMax'])])    #weatherCodeMax gives worst conditions of the day
            tomorrowHigh = float(tomorrowData['temperatureMax'])
            tomorrowHighF = str(int(tomorrowHigh * 1.8 + 32))
            tomorrowLow = float(tomorrowData['temperatureMin'])
            tomorrowLowF = str(int(tomorrowLow * 1.8 + 32))

            # Build our strings
            todayString = "Now " + nowConditions + ",\\g" + nowTemperatureF + "\\6\\w"    #todayString includes current weather, and todays high/low
            todayString += ",Today " + todayConditions + ",\\b" + todayLowF + "\\6\\w/\\r" + todayHighF + "\\6"
            tomorrowString = "Tomorrow " + tomorrowConditions + ",\\b" + tomorrowLowF + "\\6\\w/\\r" + tomorrowHighF + "\\6"

            self.mat.stringEnterBottomExitLeft(todayString, self.c.WHITE, lenModifier=6)
            self.mat.stringEnterBottomExitLeft(tomorrowString, self.c.WHITE, lenModifier=6)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            print(self.WeatherResponseData)
            self.mat.stringEnterBottomExitLeft("Error in weather widget.", self.c.RED, speed=0, delay=0, displayTime=0.3)
                

    # displays a random news headline from google news using newsAPI
    def widget_NewsHeadlines(self):
        try:
            API_DELAY = 15

            country = "us"
            APIKey = self.secrets["NewsAPI"]
            requestURL = "https://newsapi.org/v2/top-headlines?country=" + country + "&apiKey=" + APIKey

            now = int(datetime.now(timezone.utc).timestamp())
            if (now - self.last_NewsAPI_Call > (API_DELAY * 60)):
                self._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Calling NewsAPI.org API.")
                self.last_NewsAPI_Call = now
                response = requests.get(requestURL)
                if response.status_code == 200:
                    data = response.json()
                    articles = data['articles']
                    
                    self.headlines = []
                    for art in articles:
                        self.headlines.append(art['title'])

                    self.headlineCount = int(data['totalResults'])
                else:
                    self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: NewsAPI.org API Response " + response.status_code)

            # Pick a random headline to display
            headlineIndex = random.randrange(0, len(self.headlines) - 1)
            dispString = self.headlines[headlineIndex]

            self.mat.stringEnterBottomExitLeft(dispString, self.c.WHITE, speed=0.02, delay=0, displayTime=0.6)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            self.mat.stringEnterBottomExitLeft("No news right now.", self.c.WHITE, speed=0, delay=0, displayTime=0.3)           


    # displays any active NWS alerts, otherwise it shows nothing
    def widget_Alerts(self):
        try:
            # We want alerts for our area
            requestURL = "https://api.weather.gov/alerts/active/zone/" + self.secrets["NWScountyZoneID"]

            # We have to use fake headers to get the call to go through reliably
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }

            now = int(datetime.now(timezone.utc).timestamp())
            if (now - self.last_NWSAPI_Call > (self.NWSAPIDelay * 60)):
                self._log("[LOG][" + str(datetime.now(timezone.utc)) + "]: Calling NWS Alert API.")
                self.last_NWSAPI_Call = now
                response = requests.get(requestURL, headers=headers)
                if response.status_code == 200:
                    self.NWSResponseData = response.json()
                else:
                    self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: NWS Alert API Response " + response.status_code)

            # If there is an active alert, we need to check more frequently than if there are no alerts
            if len(self.NWSResponseData['features']) > 0:
                self.NWSAPIDelay = 5
            else:
                self.NWSAPIDelay = 20
            
            # Go through the alerts and display each
            for alert in self.NWSResponseData['features']:
                prop = alert['properties']
                event = prop['event']
                alertType = prop['messageType']
                severity = prop['severity']
                sender = prop['senderName']
                alertResponse = prop['response']
                headline = prop['headline']

                # Depending on the alert, we build the string differently
                dispString = ""

                if severity == 'Extreme' or severity == 'Severe':
                    dispString += "\\r" + "NWS " + event + ":" + headline
                    self.mat.stringEnterBottomExitLeft(dispString, self.c.RED, speed=0.02, delay=0, displayTime=0.1)
                    dispString = "\\r" + alertResponse
                    self.mat.stringPrint(dispString, self.c.RED)
                    time.sleep(4)
                else:
                    dispString += "\\yNWS alert:" + event
                    self.mat.stringEnterBottomExitLeft(dispString, self.c.WHITE, speed=0.02, delay=0.8, displayTime=0.1)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            self.mat.stringEnterBottomExitLeft("Error in alerts widget.", self.c.RED, speed=0, delay=0, displayTime=0.3)  


    # Displays a random fun animation on the display to keep it interesting
    def widget_Animation(self):
        # First lets pick which animation to do
        animationNumber = random.randrange(0, 5)

        if animationNumber == 0:        # Random pixels left>right, then blank screen left>right
            # fill screen black
            # columns of random pixels w/ random colors scrolls right
            # sit for just a sec
            # column of black pixels scrolls right to clear the screen
            self.mat.clearDisplay()
            for column in range(self.mat.cols):
                r = 0
                g = 0
                b = 0
                px = 0
                while px < 7:
                    if random.randrange(0, 10) > 5:
                        r = random.randrange(0, 255)
                        g = random.randrange(0,255)
                        b = random.randrange(0, 255)
                        self.mat.matrixDrawPixel(px, column, (r, g, b))
                        self.mat.matrix.show()
                    px += 1
            time.sleep(0.7)
            for column in range(self.mat.cols):
                px = 0
                while px < 7:
                    self.mat.matrixDrawPixel(px, column, (0, 0, 0))
                    self.mat.matrix.show()
                    px += 1
        elif animationNumber == 1:      # Pixel bounces around with different colors
            # pong, where a pixel bounces around for a bit
            # to start, a position and vector are chosen at random
            self.mat.clearDisplay()
            col = random.randrange(0, self.mat.cols)
            row = random.randrange(0, self.mat.rows)
            
            r = random.randrange(0, 255)
            g = random.randrange(0,255)
            b = random.randrange(0, 255)
            color = (r, g, b)

            if random.randrange(0, 10) > 5:
                colAccel = 1
            else:
                colAccel = -1
            
            if random.randrange(0, 10) > 5:
                rowAccel = 1
            else:
                rowAccel = -1


            for step in range(240):
                col += colAccel
                row += rowAccel

                # Handle bounces top and bottom
                if (row + rowAccel >= self.mat.rows) or (row + rowAccel < 0):
                    # bounced off top or bottom, invert rowAccel
                    rowAccel = rowAccel * -1
                else:
                    #random chance of flipping again
                    if random.randrange(0, 1000) > 950:
                        rowAccel = rowAccel * -1

                # handle bounces left and right
                if (col + colAccel >= self.mat.cols) or (col + colAccel < 0):
                    colAccel = colAccel * -1  
                else:
                    #random chance of flipping again
                    if random.randrange(0, 1000) > 950:
                        colAccel = colAccel * -1

                # chances of changing color
                if random.randrange(0, 100) > 60:
                    r = random.randrange(0, 255)
                    g = random.randrange(0,255)
                    b = random.randrange(0, 255)
                    color = (r, g, b)  

                self.mat.matrixDrawPixel(row, col, color)
                self.mat.matrix.show()
        elif animationNumber == 2:      # Random red pixels flashing around
            self.mat.clearDisplay()
            lastRow = 0
            lastCol = 0
            #random pixels on display
            for px in range(100):
                self.mat.matrixDrawPixel(lastRow, lastCol, (0,0,0))
                row = random.randrange(0, self.mat.rows)
                col = random.randrange(0, self.mat.cols)
                color = (255, 0, 0)
                self.mat.matrixDrawPixel(row, col, color)
                self.mat.matrix.show()
                lastRow = row
                lastCol = col
                #time.sleep(0.2)
            time.sleep(1)
            self.mat.clearDisplay()
        elif animationNumber == 3:      # Falling rain animation
            
            # use the buffer functions to make some rain (2px high) on the buffer
            # then scroll the display up to make it look like the rain is falling
            self.mat.clearBuffer()

            #draw the raindrops
            for i in range(35):
                # pick a random row within the entire buffer, leaving room at the top to clear display
                row = random.randrange(0, self.mat.bufferRows)
                #pick a random col within the range of the display
                col = random.randrange(0, self.mat.cols)

                # pick a random color
                color = (random.randrange(0,255), random.randrange(0,255), random.randrange(0, 255))

                # draw some pixels, getting dimmer as they fall
                self.mat.bufferDrawPixel(row, col, color, brightnessMod=0.1)
                self.mat.bufferDrawPixel(row + 1, col, color, brightnessMod=0.4)
                self.mat.bufferDrawPixel(row + 2, col, color, brightnessMod=0.8)
                self.mat.bufferDrawPixel(row + 3, col, color, brightnessMod=1.0)
            
            #display
            for i in range(0, 5*(self.mat.bufferRows - self.mat.rows)):
                #print("Buffer Row " + str((self.mat.bufferRows - self.mat.rows) - i))
                self.mat.bufferWindowToMatrix([(self.mat.bufferRows - self.mat.rows) - i, 0])
                time.sleep(0)
            
            self.mat.clearDisplay()
            self.mat.clearBuffer()
            time.sleep(0.4)
        elif animationNumber == 4:      # Rainbow sine wave animation
            #for test in range(100):
            freq = random.uniform(0.25, 1.0)
            amp = self.mat.rows / 2

            phaseShift = 0.1
            if random.randrange(0, 10) > 5:
                phaseShift = -1.0 * phaseShift

            # should we clear the last drawn waveform or keep it
            clearLast = True
            if random.randrange(0, 10) > 7:
                clearLast = False

            
            hsvColor = 1
            colorShift = random.uniform(0.06, 0.6)

            self.mat.clearDisplay()
            phase = 0
            # The phase shift is how the sine wave is animated
            while math.fabs(phase) < 10:

                col = 0
                #hsvColor = 1
                # Then we just draw the sine wave along the screen
                while col < self.mat.cols:
                    # clear out the last drawn pixels if we need to
                    if math.fabs(phase) > 0 and clearLast == True:
                        if phaseShift > 0:
                            self.mat.matrixDrawPixel(int(amp * (1 + math.sin(col * freq + (phase-phaseShift)))), col, self.c.BLACK)
                        elif phaseShift < 0:
                            self.mat.matrixDrawPixel(int(amp * (1 + math.sin(col * freq + (phase+math.fabs(phaseShift))))), col, self.c.BLACK)

                    row = int(amp * (1 + math.sin(col * freq + phase)))
                    self.mat.matrixDrawPixel(row, col, self.c.HsvToRgb((hsvColor/360, 1.0, 1.0)))
                    #print(f"Col {col} has color {hsvColor}")
                    if col % 2 == 0:
                        hsvColor += colorShift#(360 / self.mat.cols)
                    
                    #self.mat.matrix.show()
                    col += 1
                
                self.mat.matrix.show()
                #time.sleep(0.5)
                phase += phaseShift


    # this widget sucks, dont call it
    def widget_Hell(self):
        try:
            old = self.mat.brightness
            self.mat.setBrightness(1)
            for i in range(15):
                self.mat.matrix.fill((0,0,0))
                self.mat.matrix.show()
                self.mat.matrix.fill(self.c.WHITE)
                self.mat.matrix.show()
            self.mat.setBrightness(old)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)


    # Displays a basic red clock for about a minute
    def widget_NightClock(self):
        try:
            start = datetime.now()
            while (datetime.now() - start).total_seconds() <= 60:
                timeString = strftime("%H:%M")
                self.mat.stringPrint(timeString, self.c.RED)
                time.sleep(60)
        except Exception as ex:
            template = "An exception of type {0} occurred in {1}. Arguments:\n{2!r}"
            message = template.format(type(ex).__name__, inspect.currentframe().f_code.co_name, ex.args)
            self._log("[ERROR][" + str(datetime.now(timezone.utc)) + "]: " + message)
            # dont display anything on the matrix for an exception here, just skip
    

    # Simple method to add text to the log file for diagnostics purposes
    def _log(self, string):
        logFile = open("log.txt", "a")
        logFile.write(string + "\n")
        logFile.close()


    # This will populate our dictionary of API keys and other sensetive information
    # This keeps stuff like API keys from being pushed to version control
    # The format of the file should have one secret per line: "secret_name secret\n"
    def __getsecrets(self):
        secretsFile = open('secrets.txt', 'r')

        for line in secretsFile:
            apiName = line.split(" ")[0]
            keyVal = line.split(" ")[1].split("\n")[0]
            self.secrets[apiName] = keyVal
        secretsFile.close()
