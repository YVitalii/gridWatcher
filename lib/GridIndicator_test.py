from gridIndicator import GridIndicator
import uasyncio as asyncio
from machine import Pin
ln="[GridIndicator_test]: "
state={"offGrid":None}

grid = GridIndicator(Pin(2, Pin.OUT),state)

blinkTask=asyncio.create_task(grid.start())   

async def main():
    i=1
    while True:      
        i += 1
        print(ln+f"{i}:",end="")
        if i%10==0:
            if state["offGrid"] is None:
                state["offGrid"]=0
            print(ln+" toggling offGrid to ",not state["offGrid"])
            state["offGrid"]=not state["offGrid"]
        if i%30==0:
            print(ln+" setting offGrid to None")
            state["offGrid"]=None
            i=0
        await asyncio.sleep(1)
asyncio.run(main())

