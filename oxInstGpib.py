#import gpib as g
import serial
import time


class gpibOxInstController():#{{{
    """Controls the oxford instrument temperature controller from the prologix GPIB-USB connector. connected to ttyUSB0 and gpib address 24."""
    def __init__(self,usbnumber=0,gpibAddr=24,timeout=0.1):#{{{
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
        self.serial.write('L1'+'\r') # sets the PID values to auto, this uses tabulated valeus for the given data range.
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
        try:
            temp = float(response.split('R')[1])
        except:
            temp = False # just give back something to use 
        return temp #}}}

    def setHeater(self,heaterValue):
        """ Turn the heater control to manual and set the heater to heaterVal"""
        self.setAddr()
        self.serial.write('A0\r') # set to manual mode
        self.serial.write('O%0.1f\r'%heaterValue) # set the heater to maximum
    def setTemperature(self,temperature):#{{{
        """ Set the temperature and make sure the temperature is set."""
        self.setAddr()
        self.serial.write('A3\r') # set back to automatic mode
        comm = 'T%0.2f'%temperature+'\r'
        print comm
        self.serial.write(comm)
        time.sleep(.2)
        setTemp = float(self.readCommand('R0').split('R')[1]) # I'm not really using this but might end up doing so in the future.
        return setTemp
        #}}}

    def setTemperatureAndWait(self,temperature,tolerance=0.8):
        """ This will set the temperature and queary the actual temperature and wait until the actual temperature is within a range of the set temperature. 
        tolerance - determines the tolerance on the temperature. This is 0.2 K
        """
        setTemp = self.setTemperature(temperature) 
        actualTemp = self.readTemperature()
        if actualTemp:
            difference = abs(setTemp - actualTemp)
        else:
            difference = tolerance + 1. # just set to something larger than tolerance
        while difference > float(tolerance):
            time.sleep(.5)
            actualTemp = self.readTemperature()
            if actualTemp:
                difference = abs(setTemp - actualTemp)
                print "Waiting for temperature to equilibrate. The actual temperature is %0.2f and the set temperaure is %0.2f"%(actualTemp,setTemp)
        return actualTemp


    def close(self):#{{{
        """ close the connection """
        self.serial.close()#}}}
#}}}


