"""
This script will continuously measure the T2 via CPMG as well as record the temperature of the sample.

It will set the heater on the thermostat to maximum and kill the PID feedback.

It will do this until the maximum temperature is reached. I'm not sure how it will figure this out at the moment.

Right now you have to set permissions on /dev/ttyUSB0 and on /dev/ttyS0 to 666.
Run 'chmod 666 /dev****' as root user.

To do:
    Set heater
    Measure T2 - Measure temperature
    save real imaginary and delay spacing to file named #.npy
    save start time stop time and average temperature to file #metaData.csv
        where # is the number of the experiment
    continuously loop over until endpoint is reached, for now lets set at 240 K 

Continuously measure temperatures in a separate thread. Save new temperatures with timestamp to a file periodically. Append to a csv file.

"""


import XeprAPI
import serial
import time
import os
import numpy
import oxInstGpib as ox
import threading
import csv

# Various functions#{{{
def csvWrite(fileName,dataToWrite,flag='wb'):#{{{
    """ Write data to file given the csv filename """
    with open(fileName,flag) as csvFile:
        writer = csv.writer(csvFile,delimiter=',')
        writer.writerows(dataToWrite)
    csvFile.close()
    print "Wrote file %s"%fileName
    return None
    #}}}

def runExp(currExp,*args):#{{{
    """ Runs the xepr experiment on deck """
    currExp.aqExpRunAndWait() # this will run until the experiment is done - set this up in a thread so that the script doesn't hang so that you can record the temperature.#}}}

def readRS232(commandString,serialInstance,verbose = False):#{{{
    """ Sends string to neoptix device and returns the returned string """
    # send the character to the device
    # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
    serialInstance.write(commandString + '\r')
    out = ''
    # let's wait one second before reading output (let's give device time to answer)
    time.sleep(.5)
    while serialInstance.inWaiting() > 0:
        out += serialInstance.read(1)
    if out != '':
        if verbose:
            print ">>" + out
        return out
    else:
        if verbose:
            print "This didn't work"
        return False#}}}

def tempLog(fileName,tempConn,stopEvent,*args):#{{{
    """
    Log the temperatures with the neoptix fiberoptic sensor.
    """
    count = 0
    print fileName
    temperatureList = []
    timelist = []
    while(not stopEvent.is_set()): # this should let me stop the thread once we're golden
        ret = readRS232('t',NeopticsSer,verbose=False)
        clear = readRS232('r',NeopticsSer,verbose=False)
        try:
            tempVal = ret.split('\n')[0]
            temperatureList.append(float(tempVal))
            timelist.append((time.time())) # this will hopefully give us a more human readable time.
            print "Temperature is ", tempVal
        except:
            print "No temp this sample"
            pass
        time.sleep(.5)
        count += 1 
        # An autosave thing to save powers list every 50 points 
        if int(count/50.) - (count/50.) == 0: # if we're at a multiple of 50 counts save the list
            dataToWrite = [('time (s)','temperature (C)')] + zip(timelist,temperatureList)
            csvWrite(fileName,dataToWrite)
            print "I just saved the temperature file!"

    # once we break the while loop save the data
    dataToWrite = [('time (s)','temperature (C)')] + zip(timelist,temperatureList)
    csvWrite(fileName,dataToWrite)
#}}}
#}}}

# Make connections#{{{
# thermostat
conn = ox.gpibOxInstController()
# xepr
try:
    xepr
except:
    xepr = XeprAPI.Xepr()
print "Have Xepr instance"
currExp = xepr.XeprExperiment()
print "Received the current experiment"
# initialize the serial connection to the Neoptics device
NeopticsSer = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS
)#}}}


fullPath = '/home/xuser/Documents/ryan/data/'
metaDataFile = fullPath+'MetaData.csv'
temperatureFile = fullPath+'temperatureLog.csv'
AtTemp = False
finalTemp = 200.
count = 0
# Start the temperature log
try:
    temperatureThreadStop = threading.Event()
    temperatureLogThread = threading.Thread(target = tempLog,args = (temperatureFile,NeopticsSer,temperatureThreadStop,1))
    temperatureLogThread.start()
except Exception as errtxt:
    print errtxt

answer = False
while not answer:
    response = raw_input('type start to begin the experiment\n--> ')
    if response == 'start':
        answer = True
    else:
        answer = False
# set the heater on the thermostat
conn.setHeater(99.0)

try:
    while not AtTemp:
        """ Loop until we need to stop """
        startTime = time.time()
        # Run experiment
        currExp.aqExpRunAndWait() 
        stopTime = time.time()
        # Sync data from experiment
        currExp.aqExpSync()
        # pull the data from the experiment.
        data = xepr.XeprDataset()
        # the data and delay axis
        ordinate = data.O # this is now a two dimensional data set.
        timeVals = data.X
        # save data
        dataSet = numpy.zeros((numpy.shape(ordinate)[0]+1,numpy.shape(ordinate)[1]),dtype='complex')
        dataSet[0,:] = timeVals
        for i in range(numpy.shape(ordinate)[0]):
            dataSet[i+1,:] = ordinate[i,:]

        numpy.save(fullPath+'%i.npy'%count,dataSet) # data format in n columns 1st column is delay spacing (x axis) 2nd - n columns is complex data for y indecies. 
        # either write or append data to the csv file.
        if os.path.isfile(metaDataFile):
            dataToWrite = [(count,startTime,stopTime)]
        else:
            dataToWrite = [('exp number','start (s)','stop (s)')] + [(count,startTime,stopTime)]
        csvWrite(metaDataFile,dataToWrite,flag = 'a')


        # Check the temperature
        currTemp = conn.readTemperature()
        if currTemp:
            if currTemp >= finalTemp:
                AtTemp = True
                temperatureThreadStop.set()

        count += 1 
    # turn the temperature controller back on and cool down for next run.
    conn.setTemperature(85.0)
except (KeyboardInterrupt,SystemExit):
    temperatureThreadStop.set()
    currExp.aqExpStop()
except Exception as errtxt:
    temperatureThreadStop.set()
    currExp.aqExpStop()
    print errtxt






