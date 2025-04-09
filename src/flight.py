import asyncio
import struct

from machine import SPI, Pin, I2C
from lib.l86gps import L86GPS
from lib.rfm9x import RFM9x
from lib.bno055 import BNO055
from lib.bmp388 import DFRobot_BMP388_SPI
from src.rf import initialize_rf

class FlightComputer:
    """
    flight computer class responsible for sensor integration, data acquisition, and telemetry transmission.
    manages the rocket's navigation systems, orientation tracking, and ground communication.
    """

    gps: L86GPS  # gps module for geospatial positioning data acquisition (latitude, longitude, altitude)

    rf: RFM9x  # radio frequency transceiver module for telemetry data transmission to ground station

    bno: BNO055  # 9-dof inertial measurement unit providing acceleration, gyroscopic, and quaternion data for precise orientation tracking

    bmp: DFRobot_BMP388_SPI  # barometric pressure sensor for altitude determination and atmospheric measurements

    gps_data: dict  # storage container for the most recent valid gps coordinate and altitude information

    def __init__(self):
        """
        initialize all flight computer subsystems and sensors.
        configures communication buses, sensor parameters, and initializes data structures.
        """
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
        """
        asynchronous task that continuously acquires gps data at regular intervals.
        processes and validates incoming nmea sentences, extracting position information
        when available. updates the internal gps_data dictionary with valid coordinates.
        
        operates at 10hz polling frequency to maintain reliable data acquisition without
        overwhelming the serial interface.
        """
        while True:
            gps_values = self.gps.read_gps()
            if gps_values and gps_values['type'] == 'GPGGA' and gps_values['status'] == 'valid':
                self.gps_data = {
                    'latitude': gps_values['latitude'],
                    'longitude': gps_values['longitude'],
                    'altitude': gps_values['altitude']
                }

            await asyncio.sleep(0.1)  # 10hz polling frequency provides optimal balance between responsiveness and system stability, nothing above 0.1 of starts spazzing

    async def transmit(self):
        """
        asynchronous telemetry transmission task that periodically sends sensor data packages
        to the ground station. encodes all relevant flight parameters into a compact binary format 
        for efficient radio transmission. 
        
        operates at 20hz transmission rate to provide high-resolution flight data while
        maintaining reliable rf link performance.
        """
        while True:
            data = self.encode_transmission_data()
            if data:
                self.rf.send(data)
                print("Data sent")

            await asyncio.sleep(0.05)  # 20hz transmission frequency ensures timely delivery of critical flight parameters.

    def encode_transmission_data(self) -> bytes | None:
        """
        encodes sensor telemetry into a compact binary format suitable for radio transmission.
        
        utilizes the struct module to create a standardized binary packet containing:
        - quaternion orientation data (4 float values)
        - gps position coordinates (latitude, longitude, altitude)
        - barometric pressure reading
        - acceleration vector components (x, y, z)
        - angular velocity measurements (x, y, z)
        
        returns:
            bytes: binary packet containing all flight telemetry data
            none: if encoding fails
        """
        format_string = '<14f'  # 14 floating point values for the bno's
        return struct.pack(format_string,
                        *self.bno.quaternion(),
                           self.gps_data["latitude"], self.gps_data["longitude"], self.gps_data["altitude"],
                           0.0,
                           *self.bno.accel(),
                           *self.bno.gyro())