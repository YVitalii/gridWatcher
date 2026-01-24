from WiFi.WiFiConnection import WiFiConnection
from BlinkLED import BlinkLED
import machine
import asyncio

led=BlinkLED(2,"WiFi")

print("Starting WiFi test")

async def  main():
    # nets={"MySSID":"MyPassword"}
    
    wifi=WiFiConnection(nets,led,trace=True)
    connectionTask=asyncio.create_task(wifi.start(trace=False))
    while True:
        await asyncio.sleep(5)
        print(".")

asyncio.run(main())
