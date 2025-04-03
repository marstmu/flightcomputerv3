import asyncio
import struct

from machine import SPI, Pin, I2C
from lib.l86gps import L86GPS
from lib.rfm9x import RFM9x
from lib.bno055 import BNO055
from lib.bmp388 import DFRobot_BMP388_SPI
from src.rf import initialize_rf

class FlightComputer:

    gps: L86GPS

    rf: RFM9x

    bno: BNO055

    bmp: DFRobot_BMP388_SPI

    gps_data: dict

    def __init__(self):
        self.gps = L86GPS()
        self.rf = initialize_rf()

        bno_i2c = I2C(0, sda=Pin(4), scl=Pin(5), timeout=100_000)
        self.bno = BNO055(bno_i2c, address=0x28, crystal=True, transpose=(0, 1, 2), sign=(0, 0, 0))

        bmp_spi = SPI(1, baudrate=100000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
        self.bmp = DFRobot_BMP388_SPI(bmp_spi, Pin(9, Pin.OUT))

        self.gps_data = {
            'latitude': 0.0,
            'longitude': 0.0,
            'altitude': 0.0,
        }

    async def poll_gps(self):
        while True:
            gps_values = self.gps.read_gps()
            if gps_values and gps_values['type'] == 'GPGGA' and gps_values['status'] == 'valid':
                self.gps_data = {
                    'latitude': gps_values['latitude'],
                    'longitude': gps_values['longitude'],
                    'altitude': gps_values['altitude']
                }

            await asyncio.sleep(0.1)

    async def transmit(self):
        while True:
            data = self.encode_transmission_data()
            if data:
                self.rf.send(data)
                print("Data sent")

            await asyncio.sleep(0.05)

    def encode_transmission_data(self) -> bytes | None:
        format_string = '<14f'  # 4 quaternions, lat, lon, alt, pressure, 3 accel, 3 gyro
        return struct.pack(format_string,
                        *self.bno.quaternion(),
                           self.gps_data["latitude"], self.gps_data["longitude"], self.gps_data["altitude"],
                           0.0,
                           *self.bno.accel(),
                           *self.bno.gyro())
