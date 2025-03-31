import machine # hardware function (Pins and I2C)
import time # used if you want to put delays in the code
from bno055 import *  # imports micropython_bno055 Bosch library

# Used to Communicate with the BNO055
# 1 - i2c bus number
# sda=machine.Pin(2) - sets the general input/output to the sda (serial data line)
# scl-machine.Pin(3) - sets the general input/output to the scl (serial clock line)
# timeout=100_000 - timeout for the bno055 sensor by 100000 microseconds 
i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), timeout=100_000) #

# imu is an instance of hte BNO055 sensor
# Call methods on the imu
# i2c - allows for the bno055 to communicate with the sensor
# address 0x28 - address of the bno055 sensor (unique identifier)
# crystal=True - external crystal oscillator is being used for timing
# transpose=(0, 1, 2) - how the coordinates are arranged (x, y, z) -> (0, 1, 2)
# sign=(0, 0, 0) - no axis inversion (1 indicates an inversion on one of the axis)
imu = BNO055(i2c, address=0x28, crystal=True, transpose=(0, 1, 2), sign=(0, 0, 0))
calibrated = False

while True:
    
    time.sleep(1)
    if not calibrated
        calibrated = imu.calibrated() # shows if the sensor is fully calibrated
    
    # Test prints of Temperature, Gryo, Acceleration, Linear Acceleration, and Quaternions
    print('Temperature: {} Celcius'.format(imu.temperature())) # Temperature of the bno055 sensor
    print('Gryo: x: {:5.0f}  x: {:5.0f}  x: {:5.0f}'.format(*imu.gryo())) # Gryo of the bno055 sensor
    print('Acceleration: x:{:5.1f}  y:{:5.1f} z:{:5.1f}'.format(*imu.accel())) # Acceleration of the bno055 sensor
    print('Linear Accelertaion: x{:5.0f}  y:{:5.1f}  z: {:5.1f}'.format(*imu.lin_acc())) # Linear Acceleration of the bno055 sensor
    print('Quaternions: w: {0:5f} x {0.5f} y {0.5f} z{0.5f}'.format(*imu.quaternion())) # Quaternions of the bno055 sensor 
    
    
    










