import gc
import uasyncio as asyncio

async def start(trace=False):
    while True:
        gc.collect()
        await asyncio.sleep(10)
        if trace:
            print("[garbageCollector]:Collected")

