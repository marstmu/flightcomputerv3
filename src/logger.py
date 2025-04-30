import asyncio

class Logger:
    def __init__(self):
        self.file = open("test.txt", "w")

    async def log(self):
       while True:
           await asyncio.sleep(2)
           self.file.write("hi\n")

    async def flush(self):
        # Timer to flush
        while True:
            await asyncio.sleep(2)
            self.file.close()
            self.file = open("test.txt", "w")

