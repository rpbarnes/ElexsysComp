import gpib_eth as g
import time as timing 
import threading

# test to see if we already have control of the spectrometer components
try:
    wave = p.make_highres_waveform([('delay',100e-9)])
except:
    print "p does not exist"
    p = m.pulsegen(True,True)
try:
    yig
except:
    from yig import _yig as yig
try:
    a.run()
except:
    a = g.agilent()
try:
    fc
except:
    fc = g.field_controller()

def voltageLog(fileName,name,connection,stopEvent,*args):
    connection.setaddr(7)
    timeList = []
    voltage = []
    count = 0
    start = timing.time() 
    while (not stopEvent.is_set()):
        try:
            volt = float(multiMeter.respond('MEAS:VOLT:DC?'))
            voltage.append(volt)
        except:
            print "There is garbage coming from device, will skip this round"
        print "I just recorded this voltage: ", volt
        timeList.append(timing.time() - start)
        timing.sleep(5)
        count += 1
        if int(count/50.) - (count/50.) == 0: # if we're at a multiple of 50 counts save the list
            try:
                h5file,childnode = h5nodebypath(fileName +'/'+name,check_only = True)
                h5file.removeNode(childnode,recursive = True)
                h5file.close()
            except:
                pass
            save = nddata(array(voltage)).rename('value','t').labels(['t'],[array(timeList)])
            save.name(name)
            save.hdf5_write(fileName)
            print "I just saved the power file!"
    try:
        h5file,childnode = h5nodebypath(fileName +'/'+name,check_only = True)
        h5file.removeNode(childnode,recursive = True)
        h5file.close()
    except:
        pass
    save = nddata(array(voltage)).rename('value','t').labels(['t'],[array(timeList)])
    save.name(name)
    save.hdf5_write(fileName)
    print "I just saved the power file!"

### To track the temperature
try:
    del multiMeter
except:
    "multiMeter does not exist"

ip = '192.168.0.12'
multiMeter = g.gpib(ip)
multiMeter.setaddr(7) # address 7
fileNameVoltage = '140920Voltages.h5'
fileNameSignal = '140920Experiments.h5'
h5file,childnode = h5nodebypath(fileName,check_only = True)
children = childnode._v_children.keys()
fileList = []
for child in children:
    fileList.append(int(child.split('e')[-1]))

nextVoltageName = 'voltage' + str(max(fileList) + 1)
nextSignalName = 'Tau187T2Exp' + str(max(fileList) + 1)
h5file.close()

save = raw_input('Do you want to save this run? (yes) or (no) : ')
if save == 'yes':
    print "Saving voltage as: ", nextVoltageName
    print "Saving signal as: ", nextSignalName
    voltageStop = threading.Event()
    voltage = threading.Thread(target = voltageLog,args = (fileName,nextVoltageName,multiMeter,voltageStop,1))
    voltage.start()

freqCenter = 9.1950e9 
yig.set_mwfreq(freqCenter)
resRatio = 3363.2 / 9.4275e9 # G / Hz
fieldCenter = freqCenter * resRatio 
print fieldCenter
fc.set_width(0)
fc.set_field(round(fieldCenter,1))

phase180 = ['x','y','-x','-y']
#phase180 = ['x','-x']
phasecyc = ['x','y','-x','-y']

pulseLength = 22e-9 # this is the 90 time

pulseSpacing = r_[200e-9:4000e-9:50e-9] # range of pulse spacings
preDelay = pulseSpacing.max() + 500e-9
end180 = preDelay + 3*pulseLength + 45e-9
a.timebase(100e-9)
a.position(end180 + pulseSpacing.min())
a.setvoltage(0.01)
a.acquire(100)
scopeCapture = a.Waveform_auto()
signal = ndshape([len(scopeCapture.getaxis('t')),len(pulseSpacing),len(phasecyc),len(phase180)],['t','tau','phyc','phyc180'])
signal = signal.alloc(dtype = 'complex')
signal.labels(['t','tau','phyc','phyc180'],[scopeCapture.getaxis('t'),pulseSpacing,r_[0:len(phasecyc)],r_[0:len(phase180)]])
for spacingCount,spacing in enumerate(pulseSpacing):
    startTime = timing.time()
    print "Running pulse spacing: ", spacing
    for ph180Count,ph180 in enumerate(phase180):
        for phyCount,phase in enumerate(phasecyc):
            a.position(end180 + spacing + 75e-9) # shift the position to keep ontop of the echo
            wave = p.make_highres_waveform([('delay',preDelay - spacing),('rect',phase,pulseLength),('delay',spacing),('rect',ph180,2*pulseLength),('delay',10e-6 - preDelay - 3*pulseLength)])
            p.digitize(wave,do_normalize = True,autoGateSwitch = True, frontBuffer = 40e-9,rearBuffer = 0.0e-9,longDelay = 2000e-6)
            signal['tau',spacingCount,'phyc',phyCount,'phyc180',ph180Count] = a.Waveform_auto()
    stopTime = timing.time()
    loopTime = (stopTime - startTime)
    print "This loop took %0.2f seconds. I predict the experiment will take another %0.2f minutes"%(loopTime,(loopTime * (len(pulseSpacing) - spacingCount)/60.))

voltageStop.set()
echo = signal.copy().ft('phyc',shift = True).ft('phyc180',shift = True)
echo = echo['phyc',3,'phyc180',0]
figure()
image(echo)
title('Echo Signal')
figure()
plot(echo['tau',:])
show()

if save == 'yes':
    signal.name(nextSignalName)
    signal.hdf5_write(fileNameSignal)

    print "I save the signal as: ", fileNameSignal +'/' + nextSignalName
    print "I save the voltage as: ", fileNameVoltage +'/' + nextVoltageName
