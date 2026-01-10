import uasyncio as asyncio
from machine import Pin
from collections import deque
from micropython import const

_PERIOD = const(500) # ms
_SHORT=const(50)# ms
_LONG=const(5*70)# ms 
_QUEUE_MAXLENGTH = 5
class BlinkLED:
    def __init__(self, pin_id, name="LED"):
        # Налаштовуємо пін з підтяжкою до живлення
        self.pin = Pin(pin_id, Pin.OUT)
        self.state = self.pin.value(0)  # Поточний стан (0 - OFF)
        self.ln=name+":"
        self.active = False
        self.queue = deque((), _QUEUE_MAXLENGTH)

    # msg= "..- " = 2 short(point) → 1 _LONG(dash) → paus(space)) 
    def showMsg(self, msg=None):
        if msg is None:
            return 
        if len(self.queue) == _QUEUE_MAXLENGTH:
            print (self.ln+"WARN::Queue is crowded!!! First message deleted!")
        self.queue.append(msg)
        # print(self.ln+f"Was add message:{msg}. len(queue)={len(self.queue)}.")

    async def displayMsg(self, msg=""):
        
        self.active=True
        
        for char in msg:
            if char == ".":
                onTime =_SHORT
            elif char == "-":
                onTime = _LONG
            elif char == " ":
                onTime=0
            else:
                 continue  
            # print(self.ln+f"[{char}] = [{onTime}]")
            if onTime > 0:
                self.pin.value(1)
            await asyncio.sleep_ms(onTime)
            self.pin.value(0)
            await asyncio.sleep_ms(_PERIOD - onTime)
        self.active=False

    async def start(self):
        while True:
            if len(self.queue)>0:
                # print(self.ln+f"Queue not empty: len(queue)={len(self.queue)}")
                while  self.active:
                    await asyncio.sleep_ms(int(_PERIOD))
                await self.displayMsg(msg=self.queue.popleft())
                
            await asyncio.sleep_ms(int(_PERIOD))
