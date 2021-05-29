#!/usr/bin/env python3

import os
import sys
import random
import wave
import contextlib
from datetime import datetime, timedelta
import time

#Button/Song A is L and Button/Song B is R

def main():
    try:
        print("----------------------------------------------------")
        print("******************************************************")
        print("Welcome to the Final Playback Program for SingSparrow")
        print("******************************************************")
        print("Please make sure the singsparrow program is stopped\nbefore running the final playback.\nGo to the controller program and select stop experiment\nif you have not already.\nThen rerun this program.")
        print("Press control-C at any time to quit")
        print("----------------------------------------------------")
        yn = getYesNo("Have you already stopped the singsparrow program? (Y/N):")
        if (yn == "N"):
            print("****************************************************")
            print("Go run the controller program to stop singsparrow.")
            print("Then come back and rerun this program.")
            print("****************************************************")
            return
        else:
            baseDirPath = "/home/pi/Desktop/singsparrow/" #for pi
            #baseDirPath  = "/Users/catharineharris/Desktop/Finalsingsparrow/" #for mac
            songDirPath = baseDirPath + "songfiles/"
            song = getSongFileName(songDirPath, baseDirPath)
            print("\n----------------------------------------------------")
            lr = leftOrRightSpeaker("Enter the speaker you want the song to play out of (L/R):\n\nNote: Song A is associated with L and song B is associated with R\nso please look at the birds log file to determine which song is A\nand which song is B if you wish to play the same song\nfrom the same side for the final playback.")
            print("\n----------------------------------------------------")
            durationInMinutes = getDurationInMinutes("Enter the amount of time you wish the playback to run for\nin minutes (e.g. enter 30 for 30 minutes):")
            print("\n----------------------------------------------------")
            os.chdir(songDirPath)
            #Add a prompt to decide the duration of the playback!!! instead of hardcoded at 30 min!!!
            confirm = getYesNo("Are you ready to start the playback of song " + song + "\nfrom the " + lr + " speaker for " + str(durationInMinutes) + " minutes? (Y/N):")
            #confirm = getYesNo("Are you ready to start the playback of song " + song + " from the " + lr + "speaker?")
            if (confirm == "N"):
                print("********************************************")
                print("Cancelling. Playback was not initiated.")
                print("********************************************")
                return
            else:
                print("Playing playback of song " + song + " from the " + lr + "speaker.\nA message will appear when the playback has ended.")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print("!!!DO NOT CLOSE THIS WINDOW!!!")
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                
                playSong(song, lr, durationInMinutes)
                
                print("********************************************")
                print("             Playback ended")
                print("********************************************")
    except KeyboardInterrupt or EOFError:
        print("Quitting program")
        return

#song repeated once twice or three times to create series of bouts
#singing 1/3 to 1/2 time silence the remainder
#for 30 min of playback
def playSong(song, lr, durationInMinutes):
    fname = song + "-" + lr + ".wav"
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)

    delay = 0.2 #delay between plays in same bout
    m = 0
    startDT = datetime.now()

    #play initial bout
    n = 0
    repeatPerBout = random.randint(1,3)
    while(n < repeatPerBout):
        #os.system("afplay " + song + "-" + lr + ".wav") #for mac
        os.system("aplay " + song + "-" + lr + ".wav") #for pi
        time.sleep(delay)
        n = n+1

    while(m < durationInMinutes):
        """
        n = 0
        repeatPerBout = random.randint(1,3)
        while(n < repeatPerBout):
            os.system("aplay " + song + "-" + lr + ".wav")
            time.sleep(delay)
            n = n+1
        """
        
        #delay between bouts, plays 1/2-1/3 of the time
        d2 = random.randint(1, 10)
        d2 = 1 + (0.1 * d2)
        r = random.randint(1,3)
        delay2 = ((duration * r) + ((r-1)*0.2)) * d2
        time.sleep(delay2)
        
        #play bout
        n = 0
        repeatPerBout = random.randint(1,3)
        while(n < repeatPerBout):
            #os.system("afplay " + song + "-" + lr + ".wav") #for mac
            os.system("aplay " + song + "-" + lr + ".wav") #for pi
            time.sleep(delay)
            n = n+1

        #calculate time since start
        nowDT = datetime.now()
        dif = nowDT - startDT
        sec = dif.seconds
        ms = dif.microseconds
        m = int(sec/60)
        sec = sec - (60 * m)
        #print("minutes: " + str(m) + " seconds: " + str(sec))

def printSongFilesDir(songDirPath):
    print("\nSong Files")
    print("---------------------------------------")
    ld = os.listdir(songDirPath)
    for f in ld:
        z = f.split(".")[0].strip()
        length = len(z)
        if(z[length-2:] != "-R" and z[length-2:] != "-L"):
            print(f)
    print("---------------------------------------")

def getSongFileName(songDirPath, baseDirPath):
    os.chdir(songDirPath)
    printSongFilesDir(songDirPath)
    print("Enter the song filename you wish to use for the final playback\n(must have .wav at the end): ")
    
    while(True):
        song = input()
        length = len(song)
        if (song[length-4:] != ".wav"):
            print("Error: Incorrect file type.\nEnter a valid song filename (must have .wav at the end): ")
        elif (not os.path.isfile(song)): #song not found
            print("Error: Song file not found.\nEnter a valid song filename (must have .wav at the end): ")
        else: #create L and R channels for song if not already created
            songName = song[:length-4]

            existsAlready = os.path.isfile(songName + "-L.wav")
            if (not existsAlready):
                os.system("sox " + song + " " + songName + "-L.wav remix 1 0")
                os.system("sox " + song + " " + songName + "-R.wav remix 0 1")
            os.chdir(baseDirPath)
            return songName

def leftOrRightSpeaker(text):
    print(text)
    while(True):
        key = input()
        if (key == "L" or key == "l" or key == "left" or key == "LEFT"):
            return "L"
        elif(key == "R" or key == "r" or key == "right" or key == "RIGHT"):
            return "R"
        else:
            print("Error: invalid input. Enter L/R:")
            
def getDurationInMinutes(text):
    print(text)
    while(True):
        key = input()
        try:
            key = int(key)
            return key
        except TypeError and ValueError:
            print("Error: invalid input. Enter an integer:")

def getYesNo(text):
    print(text)
    while(True):
        key = input()
        if (key == "Y" or key == "y" or key == "yes" or key == "YES"):
            return "Y"
        elif(key == "N" or key == "n" or key == "no" or key == "NO"):
            return "N"
        else:
            print("Error: invalid input. Enter Y/N:")

main()
