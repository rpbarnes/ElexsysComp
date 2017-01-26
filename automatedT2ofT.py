"""
This will run the T2 of temperature experiment in a more automated way.

This script communicates to xepr through the API XeprAPI.

It is still necessary to setup the T2 experiment.

For now the experiment will run approximately like

--> Queary for temperature values to run, delay time between runs, and if equilibration is needed initially.

--> Pull the experiment parameters from Xepr.

--> Set temperature - either python or Bruker - no one yet has control of the oxford instruments controller.

--> Wait until temperature equilibrates.

--> Wait 20 minutes for instance so the sample temperature equilibrates.

--> Run the T2 decay experiment.

--> Log the temperature during the experiment.

--> Save the data in the defined data folder with a name according to the temperature along with the temperature data. 

--> Repeat 

Things you need to do:
    3) put code together to run the experiment defined above.

You must run this script as xuser because the root user does not have access to the xepr instance.. If this yells at you because you don't have permissions you must change the permissions of the usb connection /dev/ttyUSB0 to the prologix controller.

Do this with 'chmod 666 /dev/ttyUSB0'. You must be logged in as root user.
"""

import XeprAPI
import serial
import time
import numpy
import oxInstGpib as ox
import threading

def makeConnectionGetExperiment():#{{{
    """ Connect to xepr and get the current experiment.
        You should put in some way of checking that the current experiment is the correct one.
    """
    try:
        xepr
    except:
        xepr = XeprAPI.Xepr()
    print "Have Xepr instance"
    currExp = xepr.XeprExperiment()
    print "Received the current experiment"
    return xepr,currExp
#}}}
def runExp(currExp,*args):
    currExp.aqExpRunAndWait() # this will run until the experiment is done - set this up in a thread so that the script doesn't hang so that you can record the temperature.

def readRS232(commandString,serialInstance,verbose = False):
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
        return False


# Make the serial connection to the Neoptics device
NeopticsSer = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS
)

# Definitions
toWait = raw_input('How long should the temperature equilibrate? (min) \n --> ')
equilibrationTime = float(toWait)*60. # seconds
temperatureTolerance = 0.2

# Make connections
conn = ox.gpibOxInstController()
try:
    xepr
except:
    xepr = XeprAPI.Xepr()
print "Have Xepr instance"
currExp = xepr.XeprExperiment()
print "Received the current experiment"

"""
Running the experiment:
    1) This will start the experiment defined in xepr.
    2) Thie will check periodically to see if a scan is done.
    3) once a scan is done it will pause, store the experiment, record the temperature, and restart the experiment.

You can change it so the dimension of the y axis is user controled via python and you can save or store each run in python separately?
"""

goodAnswer = False
while not goodAnswer:
    temperatures = raw_input('Enter a list of temperatures: ')
    temperatures = eval(temperatures)
    if type(temperatures) is list:
        goodAnswer = True

for count,temperature in enumerate(temperatures):
    #if not xepr: # check for the xepr instance.
    #    xepr,currExp = makeConnectionGetExperiment()
    #scansDonePar = currExp['NbScansDone']
    #scansToDo = currExp['NbScansToDo'].value
    print "Setting to temperature %i out of %i."%(count,len(temperatures)-1)
    print "Setting temperature"
    conn.setTemperatureAndWait(temperature,tolerance=temperatureTolerance)
    print "Equilibrating for %0.1f min"%(equilibrationTime/60.)
    time.sleep(equilibrationTime)

    print "Running Experiment %i out of %i."%(count,len(temperatures)-1)
    expThread = threading.Thread(target = runExp, args=(currExp,1))
    expThread.start()
    temperatures = []
    while expThread.isAlive():
        ret = readRS232('t',NeopticsSer,verbose=False)
        clear = readRS232('r',NeopticsSer,verbose=False)
        try:
            tempVal = ret.split('\n')[0]
            temperatures.append(float(tempVal))
            print "Temperature is ", tempVal
        except:
            print "No temp this sample"



    currExp.aqExpSync()

    # pull the data from the experiment.
    data = xepr.XeprDataset()
    ordinate = data.O # This is the actual data set.
    timeVals = data.X

    numpy.save('%iK.npy'%temperature,ordinate) # this saves the data set.
    numpy.save('%iKTime.npy'%temperature,timeVals) # this saves the data set.
    numpy.save('%iKTemp.npy'%temperature,numpy.array(temperatures)) # this saves the data set.

NeopticsSer.close()
