from src.flight import FlightComputer
from lib.icm42670 import read_who_am_i, configure_sensor, set_accel_scale, set_gyro_scale

import asyncio

async def main():
    if read_who_am_i() != 0x67:
        print("ICM-42670-P not found.")
        return

    configure_sensor()
    set_accel_scale(3)  # ±16g
    set_gyro_scale(1)  # ±500 dps

    flight = FlightComputer()

    gps_task = asyncio.create_task(flight.poll_gps())
    transmit_task = asyncio.create_task(flight.transmit())

    await asyncio.gather(gps_task, transmit_task)


if __name__ == '__main__':
    asyncio.run(main())
