#import gpib as g
import serial
import time

gpibAddr = 24 # this is the address.
usbnumber = 0
timeout = .1 # the serial.readline() command relies on this so that it is quick. If the timeout is set high the readline command will just hang.


class gpibOxInstController():#{{{
    """Controls the oxford instrument temperature controller from the prologix GPIB-USB connector."""
    def __init__(self,usbnumber,gpibAddr,timeout=0.1):#{{{
        self.gpibAddr = gpibAddr
        self.serial = serial.Serial('/dev/ttyUSB%d'%usbnumber,rtscts=0,timeout=timeout)
        self.serial.write('++ifc' + '\r') # this is an interface clear command. I'm not sure that this is necessary.
        self.serial.write('++mode 1' + '\r') # set prologix to controller mode.
        self.serial.write('++addr '+str(gpibAddr) + '\r')
        self.serial.write('++auto 1' + '\r') # turn on read after write. This sets the instrument to talk mode if no commands are being issued.
        self.serial.write('++eoi 1' + '\r') # This is needed for the ox instrument, this specifies end of the command going to the instrument.
        self.serial.write('++eos 1' + '\r') # append an end of string <cr> element to commands being sent to the instrument.
        self.serial.write('++ifc' + '\r') # this is an interface clear command. I'm not sure that this is necessary.
        print "connecting to instrument.\n"
        response = self.readCommand('V')
        print "connected to ", response
        self.configInst()#}}}

    def configInst(self):#{{{
        """ Sets configuration commands for the temperature controller. """
        self.serial.write('C3'+'\r')
        self.serial.write('H3'+'\r') # sets the appropriate heater sensor
        self.serial.write('A1'+'\r') # sets the heater to auto
        #}}}

    def setAddr(self):#{{{
        """ Set the gpib address using parameter specified in init. """
        self.serial.write('++addr '+str(self.gpibAddr)+'\r')#}}}

    def readCommand(self,command):#{{{
        """ The command is sent with a carriage return. The user does not need to append carriage return to command"""
        self.setAddr()
        self.serial.write(command + '\r')
        return self.serial.readline()#}}}

    def readTemperature(self):#{{{
        """ Read temperature from instrument """
        response = self.readCommand('R3') # this reads from sensor 3
        return float(response.split('R')[1])#}}}

    def setTemperature(self,temperature):#{{{
        """ Set the temperature and make sure the temperature is set."""
        self.setAddr()
        comm = 'T%0.2f'%temperature+'\r'
        print comm
        self.serial.write(comm)
        time.sleep(.2)
        setTemp = float(self.readCommand('R0').split('R')[1])
        return setTemp
        #}}}

    def close(self):#{{{
        """ close the connection """
        self.serial.close()#}}}
#}}}

conn = gpibOxInstController(usbnumber,gpibAddr)

conn.readTemperature()

print conn.readTemperature()
