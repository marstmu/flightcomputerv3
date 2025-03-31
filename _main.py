from lib.rfm9x import *
from machine import SPI, Pin, I2C
import struct
from lib.icm42670 import read_who_am_i, configure_sensor, read_accel_data, read_gyro_data, set_accel_scale, \
    set_gyro_scale
from lib.fusion import Fusion
from lib.l86gps import L86GPS
from lib.lps22 import LPS22
import time
import os
import neopixel
import asyncio

from src.rf import transmit, initialize_rf

# Initialize sensors
fuse = Fusion()
gps = L86GPS()

# Initialize I2C bus
i2c_barometer = I2C(0, scl=Pin(9), sda=Pin(8))
lps = LPS22(i2c_barometer)
gps_values = {
    'latitude': 0.0,
    'longitude': 0.0,
    'altitude': 0.0,
    'satellites': 0,
    'status': 'invalid'
}


async def read_gps():
    global gps_values
    while True:
        gps_data = gps.read_gps()
        gps_values = {'latitude': 0.0, 'longitude': 0.0, 'altitude': 0.0}

        if gps_data and gps_data['type'] == 'GPGGA' and gps_data['status'] == 'valid':
            gps_values = {
                'latitude': gps_data['latitude'],
                'longitude': gps_data['longitude'],
                'altitude': gps_data['altitude']
            }

        await asyncio.sleep(0.1)


async def _transmit():
    global gps_values
    try:
        data_dir = "logs"
        create_directory_if_needed(data_dir)
        log_file = initialize_log_file(data_dir)
        start_time = time.ticks_ms()
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
                  miso=Pin(16))

        rfm9x = RFM9x(spi, CS, RESET, 915.0)
        rfm9x.tx_power = 14
        rfm9x.signal_bandwidth = 500000
        rfm9x.coding_rate = 5
        rfm9x.spreading_factor = 7
        rfm9x.enable_crc = True

        i = 0
        while True:
            try:
                current_time = time.ticks_ms()
                elapsed_time = time.ticks_diff(current_time, start_time) / 1000

                # Read sensors
                accel = read_accel_data()
                gyro = read_gyro_data()
                _, pressure = lps.get()

                # Update fusion without magnetometer data
                fuse.update_nomag(accel, gyro)

                # Log data to CSV
                log_sensor_data(log_file, elapsed_time, pressure, accel, gyro)

                # Transmit data
                data = encode_data(fuse.q, gps_values, pressure, accel, gyro)
                if data is not None:
                    rfm9x.send(data)
                    print("Data packet sent")

                time.sleep(0.05)

            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"Radio initialization error: {e}")


def create_directory_if_needed(directory):
    try:
        if directory not in os.listdir("/"):
            print(f"Creating directory: {directory}")
            os.mkdir(directory)
    except Exception as e:
        print(f"Error creating directory: {e}")


def initialize_log_file(data_dir):
    log_file = f"{data_dir}/sensor_log.csv"
    with open(log_file, "w") as f:
        f.write("elapsed_time,pressure,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
    return log_file


def log_sensor_data(log_file, elapsed_time, pressure, accel, gyro):
    with open(log_file, "a") as f:
        f.write(f"{elapsed_time:.3f},{pressure},{accel[0]},{accel[1]},{accel[2]},{gyro[0]},{gyro[1]},{gyro[2]}\n")


def encode_data(quaternions, gps_data, pressure, accel, gyro):
    try:
        format_string = '<4f4f3f3f'  # 4 quaternions, lat, lon, alt, pressure, 3 accel, 3 gyro
        return struct.pack(format_string,
                           quaternions[0], quaternions[1], quaternions[2], quaternions[3],
                           gps_data["latitude"], gps_data["longitude"], gps_data["altitude"], pressure,
                           accel[0], accel[1], accel[2],
                           gyro[0], gyro[1], gyro[2])
    except Exception as e:
        print(f"Encoding error: {e}")
        return None


async def main():
    if read_who_am_i() != 0x67:
        print("ICM-42670-P not found.")
        return
    # Configure IMU with specific scales
    configure_sensor()
    set_accel_scale(3)  # ±16g
    set_gyro_scale(1)  # ±500 dps

    # Initialize logging
    LED = neopixel.NeoPixel(Pin(2), 8)
    LED[0] = (0, 0, 255)
    LED.write()

    rf = initialize_rf()
    transmit_task = asyncio.create_task(transmit(rf, b""))
    gps_read_task = asyncio.create_task(gps_task())

    await asyncio.gather(transmit_task, gps_read_task)


if __name__ == '__main__':
    asyncio.run(main())

