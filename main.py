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
WIFI_CONNECTING = const ("-. ")
WIFI_DISCONNECTED = const ("-... ")
WIFI_CONNECTED = const ("-.... ")
MASTER_LOOKING_MSG = const("..-- ")
MASTER_TIMEOUT_MSG = const("..--- ")
MASTER_TIMEOUT_COUNTER_MAX=const(10)

UDP_REQ = "Hey GridWatcher!" #b"Hey GridWatcher!"
UDP_PORT=5005
STATE_TIMER=10 # ceк, Період між опитуваннями стану сервера
HTTP_PORT=3055
ln="[main.py]:"


def stop():
    while True:
        time.sleep(5)
        print (".",end="")

async def aStop(msg="."):
    while True:
        await asyncio.sleep(5)
        print (msg)

# ------------- DS18B20 -------------
from D18B20 import TemperatureSensor
temperatureSensor= TemperatureSensor(pin_id=15,interval=10000,trace=False)


# # ------------- test: DS18B20 -------------
# asyncio.run(t1.start())



# ---- realTimer -------------
from realTime import RealTime
realTimer=RealTime()

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
from WiFi.WiFiConnection import WiFiConnection
networks={"ogoGarage":"basterbelka2","ogo":"basterbelka2","Bortek2":"71216Garant","bortek_book":"71216Garant","bortek_laser":"71216Garant","bortek_solar":"71216Garant","Bortek_Security":"71216Garant"}
# Для Raspberry Pi Pico LED на 25 піні, для ESP32 зазвичай на 2
ledWiFi = Pin(2, Pin.OUT) 

connection = WiFiConnection(networks,True)

def wiFiConnecting(self,counter):
    blink.showMsg(WIFI_CONNECTING)
    # print(".",end="")

def wiFiConnected(self):
    blink.showMsg(WIFI_CONNECTED)
    print(self.ln+f"Connected to: [{self.ssid}], my IP: {self.ip}")

def wiFiDisconnected(self):
    blink.showMsg(WIFI_DISCONNECTED)
    print(self.ln+"Disconnected from:"+self.ssid)

connection.connecting =  wiFiConnecting
connection.connected =  wiFiConnected 
connection.disconnected =  wiFiDisconnected





# ----- http router ---------
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
        
        # запуск менеджера повідомлень (блимає вбудованим світлодіодом)
        #  повинен бути спочатку щоб працювала індикація
        blinkTask=asyncio.create_task(blink.start())   

        # запуск WiFi
        connectionTask=asyncio.create_task(connection.start(trace=False))
        
        # ----- start Garbage Collector --------
        asyncio.create_task(gcCollector.start(trace=False))
        
        # ----- start temperature reader -------
        temperatureTask= asyncio.create_task(temperatureSensor.start())
       

        # --- стартові налаштування майстер-серверу
        master = None 
        masterErrCounter = MASTER_TIMEOUT_COUNTER_MAX 
        
        # --- стартові налаштування  http серверу
        http=None
        
        # --- всі параметри стану зведені в цей словник --------
        state ={
            "offGrid":None,
            "T0":None,
            "T1":None,
            "time":None,
            "weekDay":None,
            "date":None,
            "heater":None,
            "accumulator":None,
            "taskT":None,
            "taskMode":None,
            "masterServer":None,
            "httpServer":None,
            }
        # print(state)
        
        # ----------  головний цикл ----------------
        while True:
            await asyncio.sleep(10)

            if temperatureSensor.ready:
                state["T0"]= temperatureSensor.getT(0)
                state["T1"]= temperatureSensor.getT(1)
            
            # # ------------- TEST STOP ------------------
            # asyncio.run(aStop(state)) # async stop for testing
            
            # виконується тільки якщо є WiFi 
            if connection.isconnected():           
                # connection established

                # -------------- http server ------------
                if http is None:
                    # Запускаємо власний http сервер
                    http = HTTPServer(port=HTTP_PORT,trace=True) 
                    http.router = mainRouter #роутер
                    asyncio.create_task(http.start())
                    state["httpServer"] = f"{connection.ip}:{HTTP_PORT}"
                    print(ln+"Started local http server on:"+state["httpServer"])
                
                #  ------------ пошук master =- сервера ----------------
                if master is None:
                    # Шукаємо головний (master) сервер
                    blink.showMsg(MASTER_LOOKING_MSG)
                    master=findServer(message=UDP_REQ,port=UDP_PORT)
                    if not master is None:
                        # Знайдено головний (master) сервер
                        state["masterServer"] = f"{master[0]}:{master[1]}"
                        print(ln+f"Found master server on: {state['masterServer']}")
                else:
                    # Головний (master) сервер готовий
                    # даємо запит на стан master сервера 
                    res=getServerStatus(master[0],port=master[1],path="/status")
                    if res is None:
                        # Error: timeout
                        blink.showMsg(MASTER_TIMEOUT_MSG)
                        masterErrCounter -=1
                        if masterErrCounter <=0 :
                            raise ValueError(ln+"Master server didn't answer 10 times!!")
                    # data is received 
                    masterErrCounter = MASTER_TIMEOUT_COUNTER_MAX
                    # Запамятовуємо стан мережі
                    state["offGrid"] = res.get("offGrid")
                    # Запалюємо/гасимо світлодіод 
                    blink.pin.value(state["offGrid"])

                # ----------- визначення реального часу ----------
                if  realTimer.ready:
                    state["time"] = realTimer.getTimeString()
                    state["date"] = realTimer.getDateString()
                    state["weekDay"] = realTimer.getWeekDay()[0]
                else:
                    # ----------- запускаємо задачу визначення реального часу
                    realTimerTask=asyncio.create_task(realTimer.start())
            print(state)



        
        
      

        
        
        
        
        
        
        
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
          
            # обробляємо графік
            state = manager.test(offGrid,currT,clockStr=res.get("time"),weekday=weekday)
            # print(state)

            await asyncio.sleep(STATE_TIMER)

        
        
       
    except Exception as e:
        # Сюди потраплять помилки з будь-якої задачі в gather
        print(ln+f"\n[Critical error]:")
        print(e)
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
  