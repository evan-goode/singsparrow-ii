#!/usr/bin/env python3

import csv
from datetime import datetime
import os
import RPi.GPIO as GPIO
import time
import random
import re
import sys
import signal

#Button/Song A is L and Button/Song B is R if reversal=False
#Button/Song A is R and Button/Song B is L if reversal=True

def main():
    
    confFileName = "singsparrow.conf"
    baseDirPath = "/home/pi/Desktop/singsparrow/"
    #baseDirPath = "/Users/catharineharris/Desktop/singsparrow/"
    confFilePath = baseDirPath + confFileName + "/"
    songDirPath = baseDirPath + "songfiles/"
    dataDirPath = baseDirPath + "data/"
    
    outFolder = ""
    
    confFileSize = os.path.getsize(confFileName)
    t = 0
    
    if (confFileSize == 0):
        return #no experiment in progress
    else:
        #experiment in progress
        while(True):
            
            #set up new day - read from conf file
            timestamp = os.path.getmtime(confFileName)
            #only read conf file if modified or if computer crashed
            #if any var editted or reversal changed it will start at beginning of next day or on restart of singsparrow if crash
            if (t != timestamp):
                dict = readConf(confFileName, baseDirPath)
            
                outFolder = dict.get("outFolder")
                songAName = dict.get("songAName")
                songBName = dict.get("songBName")
                numTimesEachSongToBePlayed = int(dict.get("numTimesEachSongToBePlayed"))
                scheduleType = dict.get("scheduleType")
                requireReturnToMiddle = dict.get("requireReturnToMiddle") #string NOT bool!!!
                delay = float(dict.get("delayBetweenPlays"))
                reversal = dict.get("reversal") #string NOT bool!!!
            
                if (reversal == "True"): #flip song A and song B
                    x = songAName
                    songAName = songBName
                    songBName = x
                
                t = timestamp
        
            #RESET VARS at start of every day
            returnedToMiddle = True #start each new day as true This one is a bool
            scheduleCompleted = False
            numTimesAPlayed = 0
            numTimesBPlayed = 0
            historyOfLast2Presses = ["0", "0"]
            song = ""
            key = ""
            ##################################
            
            currentDate = datetime.now().date()
            outFile = str(currentDate) + ".csv"
            os.chdir(dataDirPath + outFolder + "/")
            exists = os.path.isfile(outFile)
            if (not exists):
                configureOutFileForNewDay(outFolder, outFile, baseDirPath, dataDirPath)
            else: #already exists cuz program crashed
                #read from csv file to update vars to where we left off
                lastWriteTimeStr = ""
                numRows = 0
                with open(outFile, "r") as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        numRows = numRows + 1
                        #returnedToMiddle - just give the bird a free press if crash - this is already set to True above
                        numTimesAPlayed = int(row["num-times-A-played"])
                        numTimesBPlayed = int(row["num-times-B-played"])
                        historyOfLast2Presses[1] = historyOfLast2Presses[0]
                        historyOfLast2Presses[0] = row["sensor"]
                        scheduleCompleted = row["schedule-complete"]
                        if (scheduleCompleted == "True"):
                            scheduleCompleted = True
                        else:
                            scheduleCompleted = False
                        lastWriteTimeStr = row["timestamp"]

                #write last write and restart time to log file
                if(numRows == 0):
                    lwt = os.path.getmtime(outFile)
                    lwtdt = datetime.fromtimestamp(lwt)
                    lastWriteTimeStr = str(lwtdt)
                lastWriteTime = datetime.strptime(lastWriteTimeStr, "%Y-%m-%d %H:%M:%S.%f")
                writelogfile(outFolder, lastWriteTime, baseDirPath, dataDirPath)
            
            try:
                #setup GPIO
                GPIO.setmode(GPIO.BCM)
                button1pin = 23
                button2pin = 25
                irsensorpin = 4
                ledPin = 5
                GPIO.setup(button1pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(button2pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(irsensorpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(ledPin, GPIO.OUT)
                isSameDay = True
        
                while(isSameDay):
                    buttonANotPressed = GPIO.input(23)
                    buttonBNotPressed = GPIO.input(25)
                    sensorState = 0

                    if (requireReturnToMiddle == "True"):
                        sensorState = GPIO.input(4) #1 is connected 0 is broken
            
                    if (not buttonANotPressed): #button A pressed
                        if(returnedToMiddle and not scheduleCompleted):
                            #call method which returns key for which song to play, then play song on L speaker always
                            if (scheduleType == "Simple"):
                                key = simpleSchedule("A", numTimesEachSongToBePlayed, numTimesAPlayed)
                            else:
                                key = selfBalancingSchedule("A", numTimesEachSongToBePlayed, numTimesAPlayed, numTimesBPlayed, historyOfLast2Presses)
                    
                            if(key == "A"):
                                song = songAName
                                numTimesAPlayed += 1
                            elif(key == "B"):
                                song = songBName
                                numTimesBPlayed += 1
                            else: #key == "Z"
                                song = "None"
                            
                            if (key != "Z"):
                                os.chdir(songDirPath)
                                os.system("aplay " + song + "-L.wav")
                                os.chdir(baseDirPath)
                                if(requireReturnToMiddle == "True"):
                                    returnedToMiddle = False
                        else: #not returnedToMiddle or scheduleCompleted
                            song = "None"
                
                        if ((numTimesAPlayed == numTimesEachSongToBePlayed and numTimesBPlayed == numTimesEachSongToBePlayed) and not scheduleCompleted):
                            scheduleCompleted = True
                        #write to csv - no matter what - song can be None
                        logEvent(outFolder, outFile, "A", song, numTimesAPlayed, numTimesBPlayed, scheduleCompleted, baseDirPath, dataDirPath)
                        historyOfLast2Presses[1] = historyOfLast2Presses[0]
                        historyOfLast2Presses[0] = "A"

                        time.sleep(delay)
                            
                    elif (not buttonBNotPressed): #button B pressed
                        if(returnedToMiddle and not scheduleCompleted):
                            #call method which returns which song to play, then play song on R speaker always
                            if (scheduleType == "Simple"):
                                key = simpleSchedule("B", numTimesEachSongToBePlayed, numTimesBPlayed)
                            else:
                                key = selfBalancingSchedule("B", numTimesEachSongToBePlayed, numTimesAPlayed, numTimesBPlayed, historyOfLast2Presses)
                
                            if(key == "B"):
                                song = songBName
                                numTimesBPlayed += 1
                            elif(key == "A"):
                                song = songAName
                                numTimesAPlayed += 1
                            else: #key == "Z"
                                song = "None"
                            
                            if (key != "Z"):
                                os.chdir(songDirPath)
                                os.system("aplay " + song + "-R.wav")
                                os.chdir(baseDirPath)
                                if(requireReturnToMiddle == "True"):
                                    returnedToMiddle = False
                        else: #not returnedToMiddle or scheduleCompleted
                            song = "None"
    
                        if ((numTimesAPlayed == numTimesEachSongToBePlayed and numTimesBPlayed == numTimesEachSongToBePlayed) and not scheduleCompleted):
                            scheduleCompleted = True
                        #write to csv - no matter what - song can be None
                        logEvent(outFolder, outFile, "B", song, numTimesAPlayed, numTimesBPlayed, scheduleCompleted, baseDirPath, dataDirPath)
                
                        historyOfLast2Presses[1] = historyOfLast2Presses[0]
                        historyOfLast2Presses[0] = "B"
            
                        time.sleep(delay)
                        """
                        if (requireReturnToMiddle == "True"):
                            time.sleep(0.2)
                        else:
                            print("longer sleep")
                            time.sleep(delay)
                            #time.sleep(4) #sleep longer if not required to return to middle
                        """
                    elif ((requireReturnToMiddle == "True") and (not sensorState)):
                        #middle sensor broken
                        returnedToMiddle = True
                        returnedToMiddle = True
                        GPIO.output(ledPin, GPIO.HIGH)
                    elif ((requireReturnToMiddle == "True") and sensorState):
                        #middle sensor not broken
                        GPIO.output(ledPin, GPIO.LOW)
                    else: #do nothing - no button pressed
                        pass

                    #check if same date
                    nowDate = datetime.now().date()
                    if (currentDate == nowDate):
                        isSameDay = True
                    else:
                        isSameDay = False

            except KeyboardInterrupt or EOFError:
                print("Stopping experiment")
                return
            finally:
                GPIO.cleanup()


#Supporting Methods

def writelogfile(outFolder, lastWriteTime, baseDirPath, dataDirPath):
    os.chdir(dataDirPath + outFolder + "/")
    filename = "logfile" + outFolder + ".txt"
    with open(filename, "a") as file:
        nowDT = datetime.now()
        now = str(nowDT)
        file.write("Experiment restarted: " + now + "\n")
        dif = nowDT - lastWriteTime
        days = dif.days
        sec = dif.seconds
        ms = dif.microseconds
        h = int(sec/3600)
        sec = sec - (3600 * h)
        m = int(sec/60)
        sec = sec - (60 * m)
        file.write("    Time since last write (max time system was down): " + str(days) + " days " + str(h) + " hours " + str(m) + " minutes " + str(sec) + " seconds " + str(ms) + " microseconds\n")
    os.chdir(baseDirPath)

def configureOutFileForNewDay(outFolder, outFile, baseDirPath, dataDirPath):
    os.chdir(dataDirPath + outFolder + "/")
    with open(outFile, "a") as logFile:
        fieldnames = ["timestamp", "sensor", "song-played", "num-times-A-played", "num-times-B-played", "schedule-complete"]
        writer = csv.DictWriter(logFile, fieldnames)
        writer.writeheader()
    os.chdir(baseDirPath)

def readConf(confFileName, baseDirPath):
    os.chdir(baseDirPath)
    dict = {}
    with open(confFileName, "r") as file:
        for line in file:
            dict[line.split("=")[0].strip()] = line.split("=")[1].strip()
    return dict

#Log event in .csv file
def logEvent(outFolder, file, button, song, numTimesAPlayed, numTimesBPlayed, scheduleCompleted, baseDirPath, dataDirPath):
    os.chdir(dataDirPath + outFolder + "/")
    with open(file, "a") as log_file:
        writer = csv.DictWriter(log_file, fieldnames = ["timestamp", "sensor", "song-played",  "num-times-A-played", "num-times-B-played", "schedule-complete"])
        writer.writerow(
            {
                "timestamp": datetime.now(),
                "sensor": button,
                "song-played": song,
                "num-times-A-played": numTimesAPlayed,
                "num-times-B-played": numTimesBPlayed,
                "schedule-complete": scheduleCompleted
            }
        )
    os.chdir(baseDirPath)

#Editted from Evan's Code
def otherKey(key):
    if (key == "A"):
        return "B"
    else:
        return "A"

def keyPlays(key, numTimesAPlayed, numTimesBPlayed):
    if (key == "A"):
        return numTimesAPlayed
    else:
        return numTimesBPlayed

def otherPlays(key, numTimesAPlayed, numTimesBPlayed):
    if (key == "B"):
        return numTimesAPlayed
    else:
        return numTimesBPlayed

def simpleSchedule(key, numTimesEachSongToBePlayed, numTimesKeyPlayed):
    if(numTimesKeyPlayed < numTimesEachSongToBePlayed):
        return key
    else:
        return "Z"

#selfBalancingSchedule - returns which song to play - editted from Evan
def selfBalancingSchedule(key, numTimesEachSongToBePlayed, numTimesAPlayed, numTimesBPlayed, historyOfLast2Presses):
    """Attempt to balance the number of plays of each song while maintaining
        the associations between key and song"""
    
    quota = numTimesEachSongToBePlayed
    
    maximum_odds = 3 / 4
    minimum_odds = 1 / 2
    
    def compute_odds(value, maximum, minimum, halfway):
        """Exponentially decay from `maximum`, asymptotically to `minimum`,
            crossing the arithmetic mean of `maximum` and `minimum` at value =
            `halfway`"""
        difference = maximum - minimum
        return (difference / (2 ** (value / halfway))) + minimum
    
    other = otherKey(key)
    key_plays = keyPlays(key, numTimesAPlayed, numTimesBPlayed)
    other_plays = otherPlays(key, numTimesAPlayed, numTimesBPlayed)
    
    if (key_plays >= quota):
        return other
    if (other_plays >= quota):
        return key
    
    if ((key_plays < other_plays) or (historyOfLast2Presses[0] != key and historyOfLast2Presses[1] != key)):
        return key
    
    deficit = key_plays - other_plays

    odds = compute_odds(deficit, maximum_odds, minimum_odds, 1 / 4 * quota)
    return key if random.random() < odds else other

def sigterm_handler(signal, frame):
    dt1 = datetime.now()
    print("Quitting Singsparrow " + str(dt1))
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

main()
