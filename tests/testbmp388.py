from bmp388 import*
from machine import SPI, Pin
import time


# creates an object of the SPI
spi = SPI(baudrate = 100000, polarity = 1, phase = 0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
# 0 - SPI bus at zero
# baudrate = 1000000 - Baud rate to 1MHz (signal channels per second)
# Polarity = 1 - idle state of the clock is high
# phase = 0 - data is sampled on the rising edge
# bits = 8 - 8 bits per transfer
# firstbit = SPI.MSB = most significant bit is transferred first
# sck=Pin(18) - serial clock (timing for data transmission) at pin 18
# mosi=Pin(19) - master out slave in (sending data from microcontroller to the rfm95)
# miso=Pin(16) - master in slave out (recieving data from rfm95 to the mircocontroller)


# chip select Pin
CS = Pin(26, Pin.OUT)

# creates an bmp388 object using the spi object and the chip select
bmp388 = bmp388.DFRobot_BMP388_SPI(spi, CS)


while True:
    
    print("Altitude : " + bmp388.readAltitude()) # prints the altitude (without calibration)
    
    time.sleep(0.5)
    
    
    











