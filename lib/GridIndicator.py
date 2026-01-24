
import uasyncio as asyncio

class GridIndicator():
    def __init__(self, led, state):
        print("[GridIndicator]::init")
        self.led = led
        self.led.value(0)
        self.state = state
        self.ln="[GridIndicator]::"
        # print(self.ln)
        # print(self.state)
    async def start(self):
        ln=self.ln+"start()::"
        while True:
            # print(ln,end="")
            # print(self.state)
            if self.state["offGrid"] is None:
                self.led.value(not self.led.value())
            else:
                self.led.value(not self.state["offGrid"])
            await asyncio.sleep(1)