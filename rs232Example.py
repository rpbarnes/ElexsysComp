import time
import serial

def readRS232(commandString,serialInstance,verbose = False):
    # send the character to the device
    # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
    serialInstance.write(commandString + '\n')
    out = ''
    # let's wait one second before reading output (let's give device time to answer)
    time.sleep(.5)
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

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS
)
string = 'ta'

ret = readRS232(string,ser,verbose=True)
ser.close()
