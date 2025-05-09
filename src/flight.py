import asyncio
import struct
import utime
import math

from machine import SPI, Pin, I2C, UART
from lib.adafruit_gps import GPS
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

    gps: GPS  # gps module for geospatial positioning data acquisition (latitude, longitude, altitude)

    rf: RFM9x  # radio frequency transceiver module for telemetry data transmission to ground station

    bno: BNO055  # 9-dof inertial measurement unit providing acceleration, gyroscopic, and quaternion data for precise orientation tracking

    bmp: DFRobot_BMP388_SPI  # barometric pressure sensor for altitude determination and atmospheric measurements

    gps_data: dict  # storage container for the most recent valid gps coordinate and altitude information

    logger: Logger

    start_time = utime.ticks_ms()

    ALTITUDE = 200

    CHANNEL = 5

    def __init__(self):
        """
        initialize all flight computer subsystems and sensors.
        configures communication buses, sensor parameters, and initializes data structures.
        """
        # Init the GPS
        uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
        self.gps = GPS(uart)
        self.gps.send_command("PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0")
        self.gps.send_command("PMTK220,100")


        self.rf = initialize_rf()
        self.rf.node = self.CHANNEL

        bno_i2c = I2C(0, sda=Pin(4), scl=Pin(5), timeout=100_000)
        self.bno = BNO055(bno_i2c, address=0x28, crystal=True, transpose=(0, 1, 2), sign=(0, 0, 0))

        bmp_spi = SPI(1, baudrate=100000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
        self.bmp = DFRobot_BMP388_SPI(bmp_spi, Pin(9, Pin.OUT))
        self.sea_level = self.bmp.readSeaLevel(self.ALTITUDE)

        self.gps_data = {
            "lat": 0,
            "long": 0,
            "alt": 0,
            "fix": 0,
            "sats": 0,
            "hor_dilution": 0,
            "height": 0,
            "velo": 0,
            "speed": 0,
            "track_angle": 0
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
            has_data = self.gps.update()
            if has_data:
                # Check for fix
                if not self.gps.has_fix:
                    print("Waiting for fix...")

                if self.gps.latitude:
                    self.gps_data["lat"] = self.gps.latitude

                if self.gps.longitude:
                    self.gps_data["long"] = self.gps.longitude

                if self.gps.altitude_m:
                    self.gps_data["alt"] = self.gps.altitude_m

                if self.gps.fix_quality:
                    self.gps_data["fix"] = self.gps.fix_quality

                if self.gps.satellites:
                    self.gps_data["sats"] = self.gps.satellites

                if self.gps.horizontal_dilution:
                    self.gps_data["hor_dilution"] = self.gps.horizontal_dilution

                if self.gps.height_geoid:
                    self.gps_data["height"] = self.gps.height_geoid

                if self.gps.velocity_knots:
                    self.gps_data["speed"] = self.gps.velocity_knots

                if self.gps.speed_knots:
                    self.gps_data["speed"] = self.gps.speed_knots

                if self.gps.track_angle_deg:
                    self.gps_data["track_angle"] = self.gps.track_angle_deg

            await asyncio.sleep(
                0.1)  # 10hz polling frequency provides optimal balance between responsiveness and system stability, nothing above 0.1 of starts spazzing

    async def transmit(self):
        """
        asynchronous telemetry transmission task that periodically sends sensor data packages
        to the ground station. encodes all relevant flight parameters into a compact binary format
        for efficient radio transmission.

        operates at 20hz transmission rate to provide high-resolution flight data while
        maintaining reliable rf link performance.
        """
        while True:
            # get sensor data and encoded binary
            result = self.encode_transmission_data()

            if result:
                # Send the binary data
                log_data, binary_data = result
                await self.logger.log(log_data)
                self.rf.send(binary_data)

            await asyncio.sleep(
                0.05)  # 20hz transmission frequency ensures timely delivery of critical flight parameters.

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
        # get current time
        current_time = utime.ticks_ms()
        timestamp = utime.ticks_diff(current_time, self.start_time) / 1000

        quaternion = list(self.bno.quaternion())
        # Multiply by 100 for us to convert to short int
        quaternion[0] *= 100
        quaternion[1] *= 100
        quaternion[2] *= 100
        quaternion[3] *= 100
        quaternion = list(map(int, quaternion))

        # BMP altitude
        altitude = self.bmp.readCalibratedAltitude(self.sea_level)
        pressure = self.bmp.readPressure()

        # Multiply by 100 for us to convert to short int
        accel = list(self.bno.accel())
        speed = math.sqrt((accel[0] ** 2) + (accel[1] ** 2) + (accel[2] ** 2)) * 100

        accel[0] *= 100
        accel[1] *= 100
        accel[2] *= 100
        accel = list(map(int, accel))

        # Log BMP, send GPS
        log_data = [timestamp] + quaternion + [self.gps_data["lat"], self.gps_data["long"]] + [altitude, pressure] + accel + [self.gps_data["fix"], self.gps_data["sats"], self.gps_data["hor_dilution"], self.gps_data["height"], self.gps_data["velo"], self.gps_data["speed"], self.gps_data["track_angle"]]
        raw_data = [timestamp] + quaternion + [self.gps_data["lat"], self.gps_data["long"]] + [self.gps_data["alt"], pressure] + [int(speed)]

        # Pack for transmission
        # Float timestamp, 4 short int quaternions (w, x, y, z), 3 short int latitude, longitude and altitude, 1 float pressure, 1 short speed (m/s).
        format_string = "<1f4h3h1f1h"
        try:
            binary_data = struct.pack(format_string, *raw_data)
            return log_data, binary_data
        except Exception as e:
            print(e)
            return None




