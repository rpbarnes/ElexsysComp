import time as timing
import serial
import csv


def writeToFile(filename,dataSet):
    with open(filename,'w+') as csvfile:
        writer = csv.writer(csvfile,delimiter = ',')
        writer.writerows(dataSet)
    csvfile.close()

def readRS232(commandString,serialInstance,verbose = False):
    # send the character to the device
    # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
    serialInstance.write(commandString + '\r\n')
    out = ''
    # let's wait one second before reading output (let's give device time to answer)
    timing.sleep(.5)
    while ser.inWaiting() > 0:
        out += ser.read(1)
    if out != '':
        if verbose:
            print ">>" + out
        return out
    else:
        if verbose:
            print "This didn't work"
        return False

# Initialize the serial connection
# configure the serial connections (the parameters differs on the device you are connecting to)
header = '/home/xuser/xeprFiles/Data/Ryan/150628T2ExpsCheYK91CMTSL/'
filename = raw_input('Give me a file name Bitch!!! >>> ')
answerString = 'Are you sure %s is what you want to name your file?'%filename
answer = raw_input(answerString)
if answer == '': # anything but enter throws error
    pass
else:
    raise ValueError("You fucked up, try again.")


filename += '.txt'
filename = header + filename
ser = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_ODD,
	#stopbits=serial.STOPBITS_TWO,
	bytesize=serial.SEVENBITS
)
string = 'MEAS:VOLT:DC?'
ser.write('SYST:REM\r\n')
ser.flush()
timing.sleep(1)

volt = []
time = []
count = 0
countsToSave = 20
try:
    while True:
        reading = readRS232(string,ser,verbose=True)
        if reading:    
            #reading = float(reading.split('\\')[0])
            try:
                reading = float(reading)
                volt.append(reading)
                time.append(timing.time())
                count += 1
                if count > countsToSave:
                    voltageSeries = [('voltage','time (s)')] + zip(volt,time)
                    writeToFile(filename,voltageSeries)
                    print "I just wrote this shit to a file!"
                    count = 0
            except:
                print "I got a weird reading, skipping now becuase that's all I can do."
        else:
            print "Bogus Reading, trying again"
            timing.sleep(1)
except KeyboardInterrupt:
    voltageSeries = [('voltage','time (s)')] + zip(volt,time)
    writeToFile(filename,voltageSeries)
    print "Closing and writing to a file"
    ser.close()

        


