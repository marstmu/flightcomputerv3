import asyncio
import os

class Logger:
    def __init__(self, filename="flight_log.csv"):
        if os.path.exists(filename):
            # Move to the logs folder under a new name
            if not os.path.exists("logs"):
                os.mkdir("logs")

            os.rename(filename, "logs/" + filename + "." + str(time.time()))

        self.filename = filename
        self.file = open(filename, "w")
        self.write_header()

    def write_header(self):
        """Create a header for the CSV file"""
        header = "timestamp,quat_w,quat_x,quat_y,quat_z,lat,long,alt,pressure,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z"
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
            self.file.flush()

