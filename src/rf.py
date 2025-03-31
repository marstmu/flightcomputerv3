from lib.rfm9x import RFM9x
from machine import SPI, Pin, I2C


def initialize_rf() -> RFM9x:
    CS = Pin(20, Pin.OUT)
    RESET = Pin(17, Pin.OUT)
    spi = SPI(0,
              baudrate=1000000,
              polarity=0,
              phase=0,
              bits=8,
              firstbit=SPI.MSB,
              sck=Pin(18),
              mosi=Pin(19),
              miso=Pin(16)
              )

    rf = RFM9x(spi, CS, RESET, 915.0)
    rf.tx_power = 14
    rf.signal_bandwidth = 500000
    rf.coding_rate = 5
    rf.spreading_factor = 7
    rf.enable_crc = True

    return rf
