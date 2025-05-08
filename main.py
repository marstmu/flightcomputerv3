from src.flight import FlightComputer

import asyncio

async def main():
    flight = FlightComputer()

    # gps_task = asyncio.create_task(flight.poll_gps())
    transmit_task = asyncio.create_task(flight.transmit())
    flush_task = asyncio.create_task(flight.logger.flush())

    await asyncio.gather(transmit_task, flush_task)


if __name__ == '__main__':
    asyncio.run(main())
