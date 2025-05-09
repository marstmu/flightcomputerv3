import asyncio
import os
import time

class Logger:
    def __init__(self, filename="flight_log.csv"):
        self.filename = filename

        if self.path_exists(filename):
            # Open in append mode
            self.file = open(filename, "a")
        else:
            self.file = open(filename, "w")
            self.write_header()

    @staticmethod
    def path_exists(path):
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    def write_header(self):
        """Create a header for the CSV file"""
        header = "timestamp,quat_w,quat_x,quat_y,quat_z,lat,long,alt,pressure,accel_x,accel_y,accel_z,fix_quality,satellites,horizontal_dilution,height_geoid,velocity(kt),speed(kt),track_angle_deg"
        self.file.write(header + "\n")

    async def log(self, data=None):
        """Log flight data to CSV"""
        if data:
            log_line = ",".join(map(str, data))
            self.file.write(log_line + "\n")
        else: 
            empty_row = ",".join(["0"] * 15)  # Fill with zeros
            self.file.write(empty_row + "\n")

    async def flush(self):
        # Timer to flush
        while True:
            await asyncio.sleep(2)
            self.file.close()
            self.file = open(self.filename, "a")


