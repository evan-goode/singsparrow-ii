#!/usr/bin/env python3

import csv
from datetime import datetime, timedelta
import os
import re
import zipfile

def main():
    try:
        print("----------------------------------------------------")
        print("Welcome to the Controller Program for SingSparrow")
        print("Press control-C at any time to quit")
        print("----------------------------------------------------")
        confFileName = "singsparrow.conf"
        baseDirPath = "/home/pi/Desktop/singsparrow/"
        #baseDirPath = "/Users/catharineharris/Desktop/singsparrow/"
        confFilePath = baseDirPath + confFileName + "/"
        songDirPath = baseDirPath + "songfiles/"
        dataDirPath = baseDirPath + "data/"
        
        confFileSize = os.path.getsize(confFileName)
        selection = menu1(confFileSize, confFileName, baseDirPath)
        
        if (confFileSize == 0):
            if (selection == 1):
                outFolder = getValidOutFolder(baseDirPath, dataDirPath)
                songAName = configureSongFiles("A", songDirPath, baseDirPath)
                songBName = configureSongFiles("B", songDirPath, baseDirPath)
                numTimesEachSongToBePlayed = createQuota()
                schedule = configureSchedule()
                middle = requireReturnToMiddle()
                delay = getDelayBetweenPlays()
                email = configureEmailToHandleCrash()
                #need to write up and configure sending the email
            
                l1 = "outFolder=" + outFolder + "\n"
                l2 = "songAName=" + songAName + "\n"
                l3 = "songBName=" + songBName + "\n"
                l4 = "numTimesEachSongToBePlayed=" + str(numTimesEachSongToBePlayed) + "\n"
                l5 = "scheduleType=" + schedule + "\n"
                l6 = "requireReturnToMiddle=" + str(middle) + "\n"
                l7 = "delayBetweenPlays=" + str(delay)  + "\n"
                l8 =  "reversal=False\n"
                l9 = "email=" + email + "\n"
                filebuffer = [l1, l2, l3, l4, l5, l6, l7, l8, l9]
                createOutFolder(outFolder, baseDirPath, dataDirPath)
                writeConf(confFileName, filebuffer, baseDirPath)
                writelogfile(outFolder, "start", [], baseDirPath, dataDirPath)
                writeConfToLog(confFileName, outFolder, baseDirPath, dataDirPath)
                print("Current Configuration")
                print("---------------------------------------")
                printConf(confFileName, baseDirPath)
                print("---------------------------------------")
                yn = getYN("Is the current setup correct? (Y/N)")
                if (yn == "N"):
                    print("***************************************")
                    print("Canceling setup. No experiment started.")
                    print("***************************************")
                    clearFile(confFileName, baseDirPath)
                else:
                    program = "singsparrow.py"
                    #START SINGSPARROW
                    os.system("nohup python3 " + program + " &")
                    print("***************************************")
                    print("Setup successful!")
                    print("***************************************")
        
            else: #selection == 2
                print("Quitting program")
                return
    
        else: #confFileSize !=0
            if (selection == 1):
                os.chdir(dataDirPath)
                outFolder = getCurrentOutFolderName(confFileName, baseDirPath)
                outFolderPath = dataDirPath + outFolder + "/"
                os.chdir(outFolderPath)
                print("Files in " + outFolder)
                printDirFiles(outFolderPath)
        
                print("Please enter the out file you wish to read: ")
                while(True):
                    fileToRead = input()
                    if (not os.path.isfile(fileToRead)): #file not found
                        print("Error: File not found. Enter a valid filename: \n")
                    else:
                        break
                os.system("cat " + fileToRead)
                os.chdir(baseDirPath)

            elif (selection == 2):
                zipOutFolder(confFileName, baseDirPath, dataDirPath)
                print("***************************************")
                print("Success! Your data has been zipped.")
                print("However, the email feature is not working at this time.")
                print("***************************************")
                
                """
                zipEmailDeleteZip(confFile, baseDirPath, dataDirPath)
                print("***************************************")
                print("Success! Check your email for a zipfile\ncontaining the experiment's current data.")
                print("***************************************")
                """

            elif (selection == 3):
                #initiate reversal by editing conf file
                #reversal will begin the next day
                yesno = getYesNo("Are you sure you want to initiate a reversal on the current experiment?: (Enter Yes or No)")
                if (yesno == "Y"):
                    outFolder = getCurrentOutFolderName(confFileName, baseDirPath)
                    writelogfile(outFolder, "reversal", [], baseDirPath, dataDirPath)
                    reversal(confFileName, baseDirPath)
                    print("***************************************")
                    print("Reversal initiated.\nThe reversal will begin tomorrow.")
                    print("***************************************")
                else:
                    print("***************************************")
                    print("Reversal NOT initiated.")
                    print("***************************************")
        
            elif (selection == 4):
                print("Select a line to edit")
                print("---------------------------------------")
                printConfWithLineNumbers(confFileName, baseDirPath)
                quitlinenum = 8
                print(str(quitlinenum) + ": Quit")
                print("---------------------------------------")
                while(True):
                    selection = input()
                    try:
                        selection = int(selection)
                        if (selection > 0 and selection <= 7):
                            selection = selection + 1
                            break
                        elif(selection == quitlinenum):
                            print("Quitting program")
                            return
                        else:
                            print("Error: Not a valid selection number")
                    except TypeError and ValueError:
                        print("Error: Not a valid selection number")

                newInput = ""
            
                if(selection == 2):
                    newInput = configureSongFiles("A", songDirPath, baseDirPath)
                elif(selection == 3):
                    newInput = configureSongFiles("B", songDirPath, baseDirPath)
                elif(selection == 4):
                    newInput = createQuota()

                elif(selection == 5):
                    newInput = configureSchedule()
                elif(selection == 6):
                    newInput = requireReturnToMiddle()
                elif(selection == 7):
                    newInput = getDelayBetweenPlays()
                else:
                    selection = 9
                    newInput = configureEmailToHandleCrash()
                outFolder = getCurrentOutFolderName(confFileName, baseDirPath)
                changed = editConf(confFileName, selection, newInput, baseDirPath)
                if (changed[1] == changed[2]):
                    print("***************************************")
                    print("Error: You entered the same value for " + changed[0] + ".\n       No change was made.")
                    print("***************************************")
                else:
                    writelogfile(outFolder, "edit", changed, baseDirPath, dataDirPath)
                    print("***************************************")
                    print("Edit successful!\nThe edits will take effect tomorrow.")
                    print("***************************************")
                    print("Current Configuration")
                    print("---------------------------------------")
                    printConf(confFileName, baseDirPath)
                    print("---------------------------------------")
            elif (selection == 5):
                yesno = getYesNo("Are you really sure you want to end this experiment?: (Enter Yes or No)")
                if (yesno == "Y"):
                    #clear conf file
                    outFolder = getCurrentOutFolderName(confFileName, baseDirPath)
                    writelogfile(outFolder, "stop", [], baseDirPath, dataDirPath)
                    #data now finished
                    #zip data and email to user
                    #zipEmailDeleteZip(filename, baseDirPath, dataDirPath)
                    zipOutFolder(confFileName, baseDirPath, dataDirPath)
                    clearFile(confFileName, baseDirPath)
                    #stop singsparrow.py - send a kill signal - ADD THIS - or will just end at start of next day anyway
                    program = "singsparrow.py"
                    #STOP SINGSPARROW.PY
                    os.system("kill $(pgrep -f " + program +")")
                    print("***************************************")
                    print("Experiment ended. Data zipped.")
                    print("However, the email feature is not working at this time.")
                    print("***************************************")
                    """
                    print("***************************************")
                    print("Experiment ended. Data emailed to user.")
                    print("***************************************")
                    """
                else:
                    print("*********************************************")
                    print("This experiment will continue as scheduled.")
                    print("*********************************************")
            else:
                print("Quitting program")
                return
    except KeyboardInterrupt or EOFError:
        print("Quitting program")
        return

def menu1(confFileSize, confFileName, baseDirPath):
    while(True):
        
        if (confFileSize != 0):
            print("***************************************")
            print(" !!!Experiment in progress!!!")
            print("***************************************")
            print("Current Configuration")
            print("---------------------------------------")
            printConf(confFileName, baseDirPath)
            print("---------------------------------------")
            print("Menu - Please enter the number of your selection")
            print("1: Read data from an outfile")
            print("2: Zip current data and email it to the configured email")
            print("3: Initiate a reversal on the current experiment (to begin tomorrow)")
            print("4: Edit the current experiment")
            print("5: Stop the current experiment (data will also be emailed)")
            print("6: Quit")
        else:
            print("***************************************")
            print(" No experiment currently in progress ")
            print("***************************************")
            print("Menu - Please enter the number of your selection")
            print("1: Set up and start a new experiment")
            print("2: Quit")
        selection = input()
        try:
            selection = int(selection)
            if (selection == 1 or selection == 2):
                break
            if (confFileSize != 0):
                if (selection > 0 and selection <= 6):
                    break
                else:
                    print("Error: Not a valid selection number")
        except TypeError and ValueError:
            print("Error: Not a valid selection number")
    return selection

#File Methods

"""
def printDirFolders(path):
    print("---------------------------------------")
    ld = os.listdir(path)
    for f in ld:
        if(not os.path.isfile(f)):
            print(f)
    print("---------------------------------------")
"""
def printDirFiles(path):
    print("---------------------------------------")
    ld = os.listdir(path)
    for f in ld:
        if (os.path.isfile(f)):
            print(f)
    print("---------------------------------------")

def getAllFilePaths(dir, baseDirPath, dataDirPath):
    os.chdir(dataDirPath)
    filePaths = []
    for root, dirs, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            filePaths.append(filepath)
    return filePaths

def zipOutFolder(filename, baseDirPath, dataDirPath):
    outFolder = getCurrentOutFolderName(filename, baseDirPath)
    zipname = outFolder + ".zip"
    filelist = getAllFilePaths(outFolder, baseDirPath, dataDirPath)
    
    with zipfile.ZipFile(zipname, "w") as zf:
        for file in filelist:
            zf.write(file)
    return zipname

def emailZip(zipname):
    #email zip file - ADD THIS!!!
    return

def zipEmailDeleteZip(filename, baseDirPath, dataDirPath):
    zipname = zipOutFolder(filename, baseDirPath, dataDirPath)
    emailZip(zipname)
    os.system("mv " + zipname + " ~/.Trash") #move zip to trash

def renamedir(outFolder, newInput, baseDirPath, dataDirPath):
    os.chdir(dataDirPath)
    os.system("mv " + outFolder + " " + newInput)
    os.chdir(newInput)
    os.system("mv logfile" + outFolder + ".txt logfile" + newInput + ".txt")
    os.chdir(baseDirPath)

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

def clearFile(filename, baseDirPath):
    os.chdir(baseDirPath)
    with open(filename, "w"):
        pass

def getCurrentOutFolderName(filename, baseDirPath):
    os.chdir(baseDirPath)
    with open(filename, "r") as file:
        of = file.readline()
        outFolder = of.split("=")[1].strip()
    return outFolder


def writelogfile(outFolder, option, list, baseDirPath, dataDirPath):
    """
    if (outFolder != "data"):
        os.chdir("data") #change to absolute path of data later - prob can remove checks above when do that too
    os.chdir(outFolder)
    """
    os.chdir(dataDirPath + outFolder + "/")
    filename = "logfile" + outFolder + ".txt"
    dt = 0
    if (option == "stop"):
        with open(filename, "r") as file:
            line = file.readline()
            sdt = line.split(": ")[1].strip()
            dt = datetime.strptime(sdt, "%Y-%m-%d %H:%M:%S.%f")
    with open(filename, "a") as file:
        nowDT = datetime.now()
        now = str(nowDT)
        if(option == "start"):
            file.write("Experiment started: " + now + "\n")
        elif(option == "reversal"):
            file.write("Reversal initiated: " + now + "\n")
        elif(option == "edit"):
            file.write("Experiment config edited: " + now + "\n")
            file.write("    Changed: " + list[0] + " from " + list[1] + " to " + list[2] + "\n")
        else: #option == stop
            file.write("Experiment stopped: " + now + "\n")
            dif = nowDT - dt
            days = dif.days
            sec = dif.seconds
            ms = dif.microseconds
            h = int(sec/3600)
            sec = sec - (3600 * h)
            m = int(sec/60)
            sec = sec - (60 * m)
            file.write("    Experiment duration: " + str(days) + " days " + str(h) + " hours " + str(m) + " minutes " + str(sec) + " seconds " + str(ms) + " microseconds\n")
    os.chdir(baseDirPath)

def writeConfToLog(filename, outFolder, baseDirPath, dataDirPath):
    os.chdir(baseDirPath)
    with open(filename, "r") as reader:
        text = reader.readlines()
    
    os.chdir(dataDirPath + outFolder + "/")
    filename2 = "logfile" + outFolder + ".txt"
    with open(filename2, "a") as writer:
        writer.write("---------------------------------------\n")
        writer.write("Initial Configuration\n")
        writer.write("---------------------------------------\n")
        writer.writelines(text)
        writer.write("---------------------------------------\n")
    os.chdir(baseDirPath)


def printConf(filename, baseDirPath):
    os.chdir(baseDirPath)
    with open(filename, "r") as file:
        for line in file:
            print(line, end="")

def printConfWithLineNumbers(filename, baseDirPath):
    os.chdir(baseDirPath)
    with open(filename, "r") as file:
        i = -1 #0
        for line in file:
            i = i+1
            if(i > 0 and i <= 6): #i <=6
                print(str(i)+": "+line, end="")
            elif(i == 8): #8
                print("7: " + line, end="")
            else:
                pass

def reversal(filename, baseDirPath):
    os.chdir(baseDirPath)
    list = []
    with open(filename, "r") as file:
        list = file.readlines()
        length = len(list)
        line = list[length-2]
        r = line.split("=")[1].strip()
        if(r == "False"):
            list[length-2] = "reversal=True\n"
        else: #r == True
            list[length-2] = "reversal=False\n"
    writeConf(filename, list, baseDirPath)

def editConf(filename, lineNum, newInput, baseDirPath):
    os.chdir(baseDirPath)
    list = []
    with open(filename, "r") as file:
        list = file.readlines()
        length = len(list)
        line = list[lineNum-1]
        r = line.split("=")[0].strip()
        oldVal = line.split("=")[1].strip()
        if(lineNum == 4):
            newInput = str(newInput)
        if(lineNum == 6): #9 #requireReturnToMiddle
            newInput = str(newInput)
        if(lineNum == 7):
            newInput = str(newInput) #delayBetweenPlays
        list[lineNum-1] = r + "=" + newInput + "\n"
    writeConf(filename, list, baseDirPath)
    changed = [r, oldVal, newInput]
    return changed

def writeConf(filename, filebuffer, baseDirPath):
    os.chdir(baseDirPath)
    with open(filename, "w") as file:
        file.writelines(filebuffer)

def createOutFolder(outFolder, baseDirPath, dataDirPath):
    os.chdir(dataDirPath)
    os.mkdir(outFolder)
    os.chdir(baseDirPath)

#Get User Input for Configuration Methods
def getValidOutFolder(baseDirPath, dataDirPath): # put this method in singsparrow to make at start of experiment - not here?
    os.chdir(dataDirPath)
    print("Enter an output folder name: (e.g. the bird name/#)")
    
    while(True):
        outFolder = input()
        if(os.path.isdir(outFolder)):
            print("Error: This output folder already exists. Enter a valid output folder name: ")
        else:
            #os.mkdir(outFolder)
            os.chdir(baseDirPath)
            #os.chdir("../") #change to absolute path of singsparrow later
            return outFolder

def configureSongFiles(label, songDirPath, baseDirPath):
    os.chdir(songDirPath)
    printSongFilesDir(songDirPath)
    print("Enter song " + label + " filename (must have .wav at the end): ")

    while(True):
        song = input()
        length = len(song)
        if (song[length-4:] != ".wav"):
            print("Error: Incorrect file type.\nEnter a valid song " + label + " filename (must have .wav at the end): ")
        elif (not os.path.isfile(song)): #song not found
            print("Error: Song file not found.\nEnter a valid song " + label + " filename (must have .wav at the end): ")
        else: #create L and R channels for song if not already created
            songName = song[:length-4]
            
            existsAlready = os.path.isfile(songName + "-L.wav")
            if (not existsAlready):
                os.system("sox " + song + " " + songName + "-L.wav remix 1 0")
                os.system("sox " + song + " " + songName + "-R.wav remix 0 1")
            os.chdir(baseDirPath)
            return songName

def configureNumDays():
    while(True):
        numDays = input("Enter number of days to run the experiment (e.g. 60):\n")
        try:
            numDays = int(numDays)
            return numDays
        except TypeError and ValueError:
            print("Error: Not an integer")

def createQuota():
    while(True):
        numTimesEachSongToBePlayed = input("Enter the number of times each song (A and B) will be played (e.g. 30):\n")
        try:
            numTimesEachSongToBePlayed = int(numTimesEachSongToBePlayed)
            return numTimesEachSongToBePlayed
        except TypeError and ValueError:
            print("Error: Not an integer")

def configureEmailToHandleCrash():
    #regex for valid email
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    while(True):
        email = input("Enter a valid email address (to recieve experimental results\nand to be notified in case of crash):\n")
        if(re.search(regex,email)):
            return email
        else:
            print("Error: Invalid email")

def configureSchedule():
    while(True):
        print("Select the schedule type you would like to run (Enter 1 or 2):")
        print("1: Simple Schedule\n   -Button A (LEFT button) will only play song A\n   -Button B (RIGHT button) will only play song B")
        print("2: Self Balancing Schedule\n   -Button A (LEFT button) usually plays song A\n   -Button B (RIGHT button) usually plays song B\n   -This schedule will balance the bird's exposure to each song\n    even if the bird repeatedly presses the same button")
        schedule = input()
        try:
            schedule = int(schedule)
            if (schedule == 1):
                return "Simple"
            elif (schedule == 2):
                return "Self Balancing"
            else:
                print("Error: Not a valid selection number")
        except TypeError and ValueError:
            print("Error: Not an integer")

def requireReturnToMiddle():
    print("Do you want to require the bird to return to the middle of the cage\nbetween button presses? (Enter Yes or No)")
    while(True):
        
        selection = input()
        if (selection == "Yes" or selection == "YES" or selection == "yes"):
            return True
        elif (selection == "No" or selection == "NO" or selection == "no"):
            return False
        else:
            print("Please enter Yes or No: ")

def getDelayBetweenPlays():
    while(True):
        delay = input("Enter the delay between song plays in seconds\nPlease use a very small value (e.g. 0.2) if REQUIRING return to middle\nand a larger value (e.g. 3 or 4) if NOT requiring return to middle:\n")
        try:
            delay = float(delay)
            return delay
        except TypeError and ValueError:
            print("Error: Not a number")

def getYesNo(text):
    print(text)
    while(True):
        key = input()
        if (key == "Y" or key == "y" or key == "yes" or key == "YES" or key == "Yes"):
            return "Y"
        elif(key == "N" or key == "n" or key == "no" or key == "NO" or key == "No"):
            return "N"
        else:
            print("Error: invalid input. Enter Yes or No:")

def getYN(text):
    print(text)
    while(True):
        key = input()
        if (key == "Y" or key == "y" or key == "yes" or key == "YES" or key == "Yes"):
            return "Y"
        elif(key == "N" or key == "n" or key == "no" or key == "NO" or key == "No"):
            return "N"
        else:
            print("Error: invalid input. Enter Y/N:")

main()
