#  --------------- Network init ------------------
import network
from time import sleep
import uasyncio as asyncio
from machine import reset

MAXERRORS=const(10)


class WiFiConnection():

    def __init__(self,networks,led,trace=False):
        # tracing     
        self.ln="WiFiConnection::" 
        if trace:
            ln=self.ln+" __init__"    
        self.wlan = network.WLAN(network.WLAN.IF_STA) 
        self.wlan.active(True)  
        self.ssid = "empty"
        self._pwd = "empty"
        self.strength = -100
        self.led=led
        self.networks=networks
        self.ip=None
        if trace:
            print(ln+'===== networks ====== ')
            print(networks)

    def connecting(self,counter):
        # абстрактний метод (можна перевизначити в нащадках), 
        # для показування прогрес-бару в процесі підключення до WiFi
        print(".",end="")

    def connected(self):
        # абстрактний метод (можна перевизначити в нащадках), 
        # для показування стану "підключенно до WiFi"
        print(self.ln+"Connected to:",end="")
        print(self.ip)
    
    def disconnected(self):
        # абстрактний метод (можна перевизначити в нащадках), 
        # для показування стану "відключенно від WiFi"
        print(self.ln+"Disconnected!")

    async def connect(self,trace=False):
        ln=self.ln+"connect()::"  
        scan = self.wlan.scan()
        if trace:
            print(ln+"=== Scan result ===")
            print(scan)
        self.ssid = "empty"
        self._pwd = "empty"
        self.strength = -100
        for ssid, bssid, channel, rssi, authmode, hidden in scan:
            ssid=ssid.decode('utf-8')
            if trace:
                print(ln+"ssid: {:20}, rssi: {:3}".format(ssid, rssi))
            if ssid in self.networks:
                print(ln+"Network found: {}; pwd: {}; {}dB".format(ssid,self.networks[ssid],rssi))
            else:
                continue
            if rssi > self.strength:
                self.strength = rssi
                self.ssid = ssid
        if self.ssid == "empty":
            print(ln+"self.ssid=empty")
            # Тут маємо створити точку доступу, поки що помилка
            print("Network not found ")
            # await asyncio.sleep(5)
            # reset()
            # raise ValueError("Network not found !!")
            return False
        # print("========")
        
        # print(self.ssid)
        # print("========")
        self._pwd = self.networks[self.ssid]
        if trace:
            print("Selected network: {}; pwd: {}; {}dB".format(self.ssid,self._pwd,self.strength))
        self.wlan.connect(self.ssid, self._pwd)
        await asyncio.sleep(2)
        return True
        


    async def start(self,trace=False):
        ln =self.ln+"start()::"
        if trace:
            print(ln+"Started")
        errCounter=MAXERRORS
        while True:
            if not self.isconnected():
                print(f"{ln} Try connect N={errCounter}" )
                self.led.value(0)
                res = await self.connect() 
                while  res and self.wlan.status() == network.STAT_CONNECTING:
                    self.led.showMsg("-.. ")
                    print(f"{ln} status: connecting in progress")
                    errCounter -= 1
                    if errCounter<=0 :
                        break
                    await asyncio.sleep(5)               
                status = self.wlan.status()
                if not res:
                    self.led.showMsg("... ")
                    print(f"{ln} status: accesspoint not found")
                elif status == network.STAT_GOT_IP:
                    self.led.value(1)  # LED ON
                    print(f"{ln} status: connection successfull!")
                    self.ip = self.wlan.ipconfig('addr4')[0]     
                elif status ==  network.STAT_IDLE:
                    errCounter -= 1
                    self.led.showMsg("-. ")
                    print(f"{ln} no connection and no activity")                
                elif status == network.STAT_WRONG_PASSWORD:
                    self.led.showMsg("--... ")
                    print(f"{ln} status: failed due to incorrect password")
                elif status == network.STAT_NO_AP_FOUND:
                    self.led.showMsg("---.. ")
                    print(f"{ln} status: failed because no access point replied")
                elif status == network.STAT_CONNECT_FAIL:
                    self.led.showMsg("----. ")
                    print(f"{ln} status: failed due to other problems")
                    errCounter -= 1
                else:
                    self.led.showMsg("----- ")
                    print(f"{ln} status: unknown state {status}")
                if errCounter<=0 :
                    print(f"{ln} ERROR: Connection not found 30 times. Reboot.." )
                    await asyncio.sleep(2)
                    reset()
                await asyncio.sleep(5)
                continue
            if trace :
                print(ln+"Connection Ok" )
            if self.led.value()==0:
                self.led.value(1)
            await asyncio.sleep(10)
  
    def isconnected(self):
        res=self.wlan.isconnected() and self.wlan.status() == network.STAT_GOT_IP
        # print(self.ln+"isconnected()::res=")
        # print(res)
        return res
  
   

