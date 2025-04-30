import asyncio
import struct
import time

from machine import SPI, Pin, I2C
from lib.l86gps import L86GPS
from lib.rfm9x import RFM9x
from lib.bno055 import BNO055
from lib.bmp388 import DFRobot_BMP388_SPI
from src.rf import initialize_rf
from src.logger import Logger

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

    logger: Logger

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

        self.logger = Logger()

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
            # get current time
            timestamp = time.time()
            
            # get sensor data and encoded binary
            result = self.encode_transmission_data()
            
            if result:
                raw_data, binary_data = result
                log_data = [timestamp] + raw_data

                # Send the binary data
                await self.logger.log(log_data)
                self.rf.send(binary_data)
                print("Data sent")

            await asyncio.sleep(0.05)  # 20hz transmission frequency ensures timely delivery of critical flight parameters.

    def encode_transmission_data(self) -> tuple[list[float], bytes] | None:
        """
        Collects and encodes sensor telemetry.
        
        Returns:
            tuple: (raw_data, binary_data) where:
                - raw_data is a list of float values
                - binary_data is the packed binary format for transmission
            None: if encoding fails
        """
        # Collect all sensor data
        quaternion = self.bno.quaternion()
        gps_coords = [self.gps_data["latitude"], self.gps_data["longitude"], self.gps_data["altitude"]]
        pressure = 0.0  # Placeholder for pressure
        accel = self.bno.accel()
        gyro = self.bno.gyro()
        
        # Combine all data
        raw_data = list(quaternion) + gps_coords + [pressure] + list(accel) + list(gyro)
        
        # Pack for transmission
        format_string = '<14f'  # 14 floating point values
        try:
            binary_data = struct.pack(format_string, *raw_data)
            return raw_data, binary_data
        except Exception:
            return None
