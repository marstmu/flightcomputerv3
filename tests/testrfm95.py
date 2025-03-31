from micropython_rfm9x import *
from machine import SPI, Pin

CS = Pin(20, pin.OUT) # Chip Select (uses this pin for Communication with the SPI)
RESET = Pin(17, pin.OUT) # Used to reset the rfm95

spi = SPI(0, baudrate = 1000000, polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
# 0 - SPI bus at zero
# baudrate = 1000000 - Baud rate to 1MHz
# Polarity = 0 - idle state of the clock is low
# phase = 0 - data is sampled on the rising edge
# bits = 8 - 8 bits per transfer
# firstbit = SPI.MSB = most significant bit is transferred first
# sck=Pin(18) - serial clock (timing for data transmission) at pin 18
# mosi=Pin(19) - master out slave in (sending data from microcontroller to the rfm95)
# miso=Pin(16) - master in slave out (recieving data from rfm95 to the mircocontroller)


# frequency
FREQUENCY = 915

# instance of the rfm9x
rfm95 = RFM9x(spi, CS, RESET, FREQUENCY)


# transmitting power in db
rfm95.tx_power = 14

while True:
    
    # receive data in byte format (bytearray)
    packet = rfm95.receive()
    
    
    if packet is None:
        print("There is no data being receive. Waiting...")
        
    else:
        
        # this is printing out the packet in bytearray
        print("Receving (bytearray form): {}".format(packet)) 
        
        # str(packet, "ascii") - converts from btye array to a string 
        print("Receving (String form): {}".format(str(packet, "ascii")))
        
        
        # rfm95.last_rssi - signal strength 
        print("Signal Strength: {}".format(rfm95.last_rssi)) 
        
        
        
                
        
    
    




