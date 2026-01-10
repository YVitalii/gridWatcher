from machine import Pin
import machine
import time
import uasyncio as asyncio
# from udp_server import UDPServer
from http_server import HTTPServer
from findServer import findServer
from httpClient import getServerStatus
from genFunc import toSeconds
import ujson


# повідомлення про стан
WIFI_CONNECTING = const ("-.. ")
WIFI_DISCONNECTED = const ("-... ")
WIFI_CONNECTED = const ("-. ")
SERVER_LOOKING = const("..-- ")
SERVER_TIMEOUT = const("..--- ")


UDP_REQ = "Hey GridWatcher!" #b"Hey GridWatcher!"
UDP_PORT=5005
STATE_TIMER=10 # ceк, Період між опитуваннями стану сервера
HTTP_PORT=3055
ln="[main.py]:"


def stop():
    while True:
        time.sleep(1)
        print (".",end="")


# ------------- DS18B20 -------------
from D18B20 import TemperatureSensor
t1= TemperatureSensor(pin_id=15,interval=10000,trace=False)
curT = None #поточна температура

# # ------------- test: DS18B20 -------------
# asyncio.run(t1.start())



#  ------------- OUTs ------------
heater = Pin(13, Pin.OUT, drive=Pin.DRIVE_1) # 10mA R=60 Ohm
accumulator = Pin(12, Pin.OUT, drive=Pin.DRIVE_1) # 10mA R=60 Ohm
heater.value(0)
accumulator.value(0)
# while True:
#     heater.value( not heater.value())
#     accumulator.value( not accumulator.value())
#     time.sleep(1)

# ------------ manager ---------------
from Manager import Manager
manager=Manager(
    heater,
    accumulator,
    dT=1,
    minT=6,
    lowT=10,
    normT=15,
    highT=18,
    trace=True
    )



# ---------- blinkLED --------------
from  BlinkLED import BlinkLED
blink=BlinkLED(2, "State")
# blink.showMsg(".- .- ")
# blink.showMsg("..- ..- ")
# blink.showMsg("...- ...- ")
# blink.showMsg("...-- ...-- ")
# blink.showMsg("...--- ...--- ")
# asyncio.run(blink.start())

# stop()



# -------   WiFi --------------------
from WiFiConnection import WiFiConnection
networks={"ogoGarage":"basterbelka2","ogo":"basterbelka2","Bortek2":"71216Garant","bortek_book":"71216Garant","bortek_laser":"71216Garant","bortek_solar":"71216Garant","Bortek_Security":"71216Garant"}
# Для Raspberry Pi Pico LED на 25 піні, для ESP32 зазвичай на 2
ledWiFi = Pin(2, Pin.OUT) 

connection = WiFiConnection(networks,True)

def wiFiConnecting(self,counter):
    blink.showMsg(WIFI_CONNECTING)
    print(".",end="")

def wiFiConnected(self):
    blink.showMsg(WIFI_CONNECTED)
    print(self.ln+"Connected to: "+self.ssid)

def wiFiDisconnected(self):
    blink.showMsg(WIFI_DISCONNECTED)
    print(self.ln+"Disconnected from:"+self.ssid)

connection.connecting =  wiFiConnecting
connection.connected =  wiFiConnected 
connection.disconnected =  wiFiDisconnected





# ----- router ---------
def mainRouter(request):
    print(ln+"MainRouter: req=")
    print(request)
    # Проста маршрутизація
    if "GET /status" in request:
        state=manager.state
        data = {
            "weekday": state[0],
            "clockStr": state[1],
            "taskT": state[2],
            "currT": state[3],
            "heater": state[4],
            "accumulator": state[5]
            }
        body = ujson.dumps(data)
        content_type = "application/json"
    elif "GET /start" in request:
        body = '{"command": "start", "result": "success"}'
        content_type = "application/json"
    else:
        body = "<h1>MicroPython Server</h1><p>Use /status or /start</p>"
        content_type = "text/html"

    return (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Connection: close\r\n\r\n"
        + body
    ) 
# ---- збиральник сміття
import gcCollector

# ---- графік роботи ---
from Manager import Manager
manager = Manager(heater,accumulator, dT=1,minT=6,lowT=10,normT=15,highT=18)



# -------  main  -------
async def main():
    try:
        connectionTask=asyncio.create_task(connection.start(trace=False))
        blinkTask=asyncio.create_task(blink.start())
        # 1. Чекаємо на підключення до WiFi 
        blink.showMsg(WIFI_CONNECTING)
        while not connection.isconnected():
            print("\nWaiting for WiFi connection...")
            await asyncio.sleep(3)
        print(ln+f"Network ready IP: {connection.ip}")
        

        # 2. Шукаємо сервер
        master = None
        errCounter=10
        while master is None:
            master=findServer(message=UDP_REQ,port=UDP_PORT)
            blink.showMsg(SERVER_LOOKING)
            errCounter = errCounter-1
            if (errCounter<=0):
                print(ln+"Server not found. Reboot...")
                machine.reset() 
            
            await asyncio.sleep(3)
        print(ln+"Master server address:",end="")
        print(master)
        errCounter=10

        # ----- start temperature reader -------
        asyncio.create_task(t1.start())
        
        # ----- start Garbage Collector --------
        asyncio.create_task(gcCollector.start(trace=False))
        
        # Запускаємо сервер
        http = HTTPServer(port=HTTP_PORT,trace=True) 
        http.router = mainRouter #роутер
        print(ln+f"Starting own http server...address={connection.ip}:{HTTP_PORT}")
        asyncio.create_task(http.start())
        
        # -----------------запит стану сервера
        while True:
            res=getServerStatus(master[0],port=master[1],path="/status")
            print(ln+"Server status=",end="")
            print(res)
            if res is None :
                errCounter=errCounter-1
                if (errCounter<=0):
                    print(ln+"Server not answered 10 times. Reboot...")
                    machine.reset() 
                await asyncio.sleep(STATE_TIMER)
                continue
            # reset counter
            errCounter=10

            # стан мережі
            offGrid= int(res.get("offGrid"))
            # print(ln + "offGrid="+str(offGrid))

            # день тижня  0 = понеділок
            weekday = int(res.get("weekday")[1])
            # print(ln + "res.get('weekday')="+str(res.get("weekday")))
            # print(ln + "weekday="+str(weekday))
            
            # # кількість секунд від початку доби 
            # clock = res.get("time")
           
            
            # індикація
            ledWiFi.value(offGrid)
            
            # считуємо температуру
            currT = t1.getT()       
            
            # обробляємо графік
            state = manager.test(offGrid,currT,clockStr=res.get("time"),weekday=weekday)
            # print(state)

            await asyncio.sleep(STATE_TIMER)

        
        
       
    except Exception as e:
        # Сюди потраплять помилки з будь-якої задачі в gather
        print(ln+f"\n[Critical error]: {e}")
        
        # Даємо трохи часу, щоб повідомлення встигло вийти в термінал
        time.sleep(2)
        
        print(ln+"Reboot...")
        machine.reset() # Фізичне перезавантаження контролера
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(ln+"Stopping..")

# while True:
#     led.on()
#     time.sleep(0.5)
#     led.off()
#     time.sleep(0.5)
  