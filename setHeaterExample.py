import oxInstGpib as ox
import time
conn = ox.gpibOxInstController()

conn.setHeater(80.0)
time.sleep(10)

conn.setTemperature(85.0)


