DEVELOPMENT=const(1)# Встановити в 1 для режиму розробки, 0 - для робочого режиму
# WiFi  мережі
networks={"ogoGarage":"basterbelka2","ogo":"basterbelka2","Bortek2":"71216Garant","bortek_book":"71216Garant","bortek_laser":"71216Garant","bortek_solar":"71216Garant","Bortek_Security":"71216Garant"}
# networks={"ogoGarage":"basterbelka2","ogo":"basterbelka2"}
from machine import Pin
import machine
import time
import uasyncio as asyncio
# from udp_server import UDPServer
from http_server import HTTPServer
from findServer import findServer
from httpClient import getServerStatus
import ujson
# from microdot import Microdot

import ramInfo
import flashInfo

# повідомлення про стан

MASTER_LOOKING_MSG = const("..-- ")
MASTER_TIMEOUT_MSG = const("..--- ")
MASTER_TIMEOUT_COUNTER_MAX=const(10)

UDP_REQ = "Hey GridWatcher!" #b"Hey GridWatcher!"
UDP_PORT=5005
STATE_TIMER=10 # ceк, Період між опитуваннями стану сервера
HTTP_PORT=3055
#  для врахування типу реле low/high 
HEATER_ON=const(0)
HEATER_OFF=const(1)

ln="[main.py]:"

# --- всі параметри стану зведені в цей словник --------
state ={
    "offGrid":None,
    "T0":None,
    "T1":None,
    "time":None,
    "weekDay":None,
    "date":None,
    "heater":0,
    "taskT":{
        "min":6, 
        "mid":15, 
        "max":20
        },
    "taskMode":None,
    "masterServer":None,
    "httpServer":None,
    }
if DEVELOPMENT: 
    print("state=",end="")
    print(state)






def stop():
    while True:
        time.sleep(5)
        print (".",end="")

async def aStop(msg="."):
    while True:
        await asyncio.sleep(5)
        print (msg)

# from requestToDict import parseRequest 
# dict=parseRequest("GET /set?taskT={min:10,mid:20,max:30}&taskTmax=30&taskTmid=20 HTTP/1.1")
# print(dict)
# stop()

# ---- test WiFi ----
# import WiFi.WiFi_test as testWiFi
# stop()

# ------------- DS18B20 -------------
from D18B20 import TemperatureSensor
temperatureSensor= TemperatureSensor(pin_id=15,interval=10000,trace=False)


# # ------------- test: DS18B20 -------------
# asyncio.run(t1.start())



# ---- realTimer -------------
from realTime import RealTime
realTimer=RealTime()

#  ------------- OUTs ------------

heater = Pin(12, Pin.OUT, drive=Pin.DRIVE_1) # 10mA R=60 Ohm
heater.value(HEATER_OFF)

# while True:
#     heater.value( not heater.value())
#     heater.value( not heater.value())
#     time.sleep(1)

#  ------------ GridIndicator --------------
from GridIndicator import GridIndicator
gridLed = GridIndicator(Pin(13, Pin.OUT, drive=Pin.DRIVE_1),state) # 10mA R=60 Ohm
gridLedTask=asyncio.create_task(gridLed.start()) 

# # ------------ manager ---------------
# from Manager import Manager
# manager=Manager(
#     heater,
#     dT=1,
#     minT=6,
#     lowT=10,
#     normT=15,
#     highT=18,
#     trace=True
#     )



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
# networks={"wrongSSID":"wrongPassword"} #test: not found any wifi 
# networks={"wrongSSID":"wrongPassword","Bortek2":"wrongPassword"} #test: wrong data in wifi 



# Для Raspberry Pi Pico LED на 25 піні, для ESP32 зазвичай на 2
# wifi_led = BlinkLED(2, "WiFi")
connection = WiFiConnection(networks,BlinkLED(2, "WiFi"),True)

from setState import setState

# ----- http router ---------
def mainRouter(req):
    trace=True
    body=None
    if trace:
        print(ln+"MainRouter: req=")
        print(req)
    # Проста маршрутизація
    if req['method']=='OPTIONS':
        # Відповідь на preflight запит CORS
        return (
            "HTTP/1.1 200 OK\r\n"
            "Access-Control-Allow-Origin: *\r\n" # Дозволяємо доступ з будь-якого джерела
            "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type\r\n"
            "Connection: close\r\n\r\n")
    if req['method']=='GET':
        if req['path']=='/status':
            body = ujson.dumps(state)
            content_type = "application/json"
    if req['method']=='POST':
        body=setState(req["data"],state)
        body= ujson.dumps(body)
        content_type = "application/json" 
    if body is None:
        body = "<h1>MicroPython Grid watcher. </h1> <p> Use GET /status or POST /set </p>"
        content_type = "text/html"
    return (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Access-Control-Allow-Origin: *\r\n" # Дозволяємо доступ з будь-якого джерела
        "Connection: close\r\n\r\n"
        + str(body)
    ) 

# ---- збиральник сміття
import gcCollector
asyncio.create_task(gcCollector.start(trace=False))

# ---- графік роботи ---
# from Manager import Manager
# manager = Manager(heater,heater, dT=1,minT=6,lowT=10,normT=15,highT=18)



# -------  main  -------
async def main():
    try: 

        # запуск WiFi
        connectionTask=asyncio.create_task(connection.start(trace=False))
              
        # ----- start temperature reader -------
        temperatureTask= asyncio.create_task(temperatureSensor.start())
       
        # --- стартові налаштування майстер-серверу
        master = None 
        masterErrCounter = MASTER_TIMEOUT_COUNTER_MAX 
        
        # --- стартові налаштування  http серверу
        http=None
                
        #  ------------ вмикаємо акумулятор тепла, якщо далі буде якась помилка -----------
    

        # ----------  головний цикл ----------------
        while True:
            await asyncio.sleep(20)
            ln = f"[main.py]:{state['time']}::"
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
                    http = HTTPServer(port=HTTP_PORT,trace=False) 
                    http.router = mainRouter #роутер
                    asyncio.create_task(http.start())
                    state["httpServer"] = f"{connection.ip}:{HTTP_PORT}"
                    print(ln+"Started local http server on:"+state["httpServer"])
                
                #  ------------ пошук master-сервера ----------------
                if master is None:
                    # Шукаємо master-сервер
                    # blink.showMsg(MASTER_LOOKING_MSG)
                    master=findServer(message=UDP_REQ,port=UDP_PORT)
                    if not master is None:
                        # Знайдено головний (master) сервер
                        state["masterServer"] = f"{master[0]}:{master[1]}"
                        print(ln+f"Found master server on: {state['masterServer']}")
                else:
                    # master-cервер готовий
                    # даємо запит на стан master сервера 
                    res=getServerStatus(master[0],port=master[1],path="/status")
                    if res is None:
                        # Error: timeout
                        # blink.showMsg(MASTER_TIMEOUT_MSG)
                        masterErrCounter -=1
                        print(ln+f"Master timeout error counter = {masterErrCounter}")
                        if masterErrCounter <=0 :
                            raise ValueError(ln+"Master server didn't answer 10 times!!")
                    else:
                        # data is received 
                        masterErrCounter = MASTER_TIMEOUT_COUNTER_MAX
                        # Запамятовуємо стан мережі
                        try:
                            state["offGrid"] = int(res.get("offGrid"))
                            state["heater"] = 0 if (state["offGrid"] is None or state["offGrid"]==1) else 1
                            # Запалюємо/гасимо світлодіод 
                            # blink.pin.value(state["offGrid"])
                           

                        except Exception as e:
                            print(ln+f"Непередбачена помилка: {e}") 

                # ----------- визначення реального часу ----------
                if  realTimer.ready:
                    state["time"] = realTimer.getTimeString()
                    state["date"] = realTimer.getDateString()
                    state["weekDay"] = realTimer.getWeekDay()[0]
                else:
                    # ----------- запускаємо задачу визначення реального часу
                    realTimerTask=asyncio.create_task(realTimer.start())
            t0=state["T0"]
            if (not t0 is None):
                if t0 <= state["taskT"]["min"]:
                    state["heater"] = 1
                    print(ln+f'[main.py]: heater ON, T0={t0} <= {state["taskT"]["min"]}=taskTmin')
                elif t0 >= state["taskT"]["max"]:
                    state["heater"] = 0
                    print(ln+f'[main.py]: heater OFF, T0={t0} >= {state["taskT"]["max"]}=taskTmax')
            heater.value(HEATER_ON if state["heater"] else HEATER_OFF)
            if DEVELOPMENT:
                ramInfo.getInfo()
            # print(state)      
       
    except Exception as e:
        # Сюди потраплять помилки з будь-якої задачі в gather
        print(ln+f"\n[Critical error]:")
        print(e)
        # Даємо трохи часу, щоб повідомлення встигло вийти в термінал
        time.sleep(2)
        print ("Current state:")
        print(state)
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
  