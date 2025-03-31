import asyncio
import neopixel

from machine import Pin

async def change_led():
    """Ammar and Nathan thought it would be funny to make police lights."""
    turn = 0
    led = neopixel.NeoPixel(Pin(2), 8)
    while True:
        if turn == 0:
            led[0] = (0, 0, 255)
            turn = 1
        elif turn == 1:
            led[0] = (255, 0, 0)
            turn = 0

        led.write()

        await asyncio.sleep(0.5)