from lib.adafruit_gps import GPS
from machine import UART, Pin
import time


def main():
    # Initialize GPS module with default pins (UART1, TX=0, RX=1)
    uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
    gps = GPS(uart)
    gps.send_command("PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0")
    gps.send_command("PMTK220,1000")
    print("GPS Module initialized. Waiting for data...")

    while True:
        # Read GPS data
        has_data = gps.update()

        if has_data:
            if not gps.has_fix:
                print("Waiting for fix...")
                continue
            print("\nGPS Position:")
            print(f"Latitude: {gps.latitude}°")
            print(f"Longitude: {gps.longitude}°")
            print(f"Altitude: {gps.altitude_m} m")
            print(f"Satellites: {gps.satellites}")
            print(f"Fix Quality: {gps.fix_quality}")

        # 1 Hz ig
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")