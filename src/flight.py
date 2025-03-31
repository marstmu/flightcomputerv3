import asyncio
import struct

from machine import SPI, Pin, I2C
from lib.l86gps import L86GPS
from lib.lps22 import LPS22
from lib.rfm9x import RFM9x
from lib.fusion import Fusion
from src.rf import initialize_rf
from lib.icm42670 import read_accel_data, read_gyro_data

class FlightComputer:

    gps: L86GPS

    rf: RFM9x

    fusion: Fusion

    gps_data: dict

    lps: LPS22

    def __init__(self):
        self.gps = L86GPS()
        self.rf = initialize_rf()
        self.fusion = Fusion()

        i2c_barometer = I2C(0, scl=Pin(9), sda=Pin(8))
        self.lps = LPS22(i2c_barometer)

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
            # TODO (Noah): I don't like how ICM is global
            accel = read_accel_data()
            gyro = read_gyro_data()
            # Temp, pressure
            _, pressure = self.lps.get()

            self.fusion.update_nomag(accel, gyro)
            data = self.encode_transmission_data(pressure, accel, gyro)
            if data:
                self.rf.send(data)
                print("Data sent")

            await asyncio.sleep(0.05)

    def encode_transmission_data(self, pressure, accel, gyro) -> bytes | None:
        format_string = '<14f'  # 4 quaternions, lat, lon, alt, pressure, 3 accel, 3 gyro
        q = self.fusion.get_q()
        return struct.pack(format_string,
                        q[0], q[1], q[2], q[3],
                           self.gps_data["latitude"], self.gps_data["longitude"], self.gps_data["altitude"],
                           pressure,
                           accel[0], accel[1], accel[2],
                           gyro[0], gyro[1], gyro[2])
