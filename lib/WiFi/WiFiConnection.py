#  --------------- Network init ------------------
import network
from time import sleep
import uasyncio as asyncio
from machine import reset

class WiFiConnection():

    def __init__(self,networks,trace=False):
        # tracing     
        self.ln="WiFiConnection::" 
        if trace:
            ln=self.ln+" __init__"    
        self.wlan = network.WLAN(network.WLAN.IF_STA) 
        self.wlan.active(True)  
        self.ssid = "empty"
        self._pwd = "empty"
        self.strength = -100
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
            return None
        # print("========")
        
        # print(self.ssid)
        # print("========")
        self._pwd = self.networks[self.ssid]
        if trace:
            print("Selected network: {}; pwd: {}; {}dB".format(self.ssid,self._pwd,self.strength))
        self.wlan.connect(self.ssid, self._pwd)
        counter = 20
        print(ln+"Connecting")
        while not self.wlan.isconnected():
            self.connecting(self,counter)        
            counter = counter - 1
            if counter == 0:
                print("Not connected after 10 times.Reboot after 5 minutes...")
                await asyncio.sleep(5*60)
                reset()
            await asyncio.sleep(3)
        self.ip = self.wlan.ipconfig('addr4')[0]
        # print(ln+"self.ip=")
        # print(self.ip)
        self.connected(self)


    async def start(self,trace=False):
        ln =self.ln+"start()::"
        if trace:
            print(ln+"Started")
        errCounter=30
        while True:
            if not self.isconnected():
                self.disconnected(self)
                print(f"{ln} Try connect N={errCounter}" )
                await self.connect()               
                status = self.wlan.status()
                if status == network.STAT_GOT_IP:
                    print(f"{ln} status: connection successfull!")
                elif status ==  network.STAT_IDLE:
                    errCounter -= 1
                    print(f"{ln} no connection and no activity")
                elif status == network.STAT_CONNECTING:
                    print(f"{ln} status: connecting in progress")
                elif status == network.STAT_WRONG_PASSWORD:
                    print(f"{ln} status: failed due to incorrect password")
                elif status == network.STAT_NO_AP_FOUND:
                    print(f"{ln} status: failed because no access point replied")
                    errCounter -= 1
                elif status == network.STAT_CONNECT_FAIL:
                    print(f"{ln} status: failed due to other problems")
                    errCounter -= 1
                else:
                    print(f"{ln} status: unknown state {status}")
                if errCounter<=0 :
                    print(f"{ln} ERROR: Connection not found 30 times. Reboot.." )
                    await asyncio.sleep(2)
                    reset()
                await asyncio.sleep(10)
                continue
            if trace :
                print(ln+"Connection Ok" )
            await asyncio.sleep(10)
  
    def isconnected(self):
        res=self.wlan.isconnected() and self.wlan.status() == network.STAT_GOT_IP
        # print(self.ln+"isconnected()::res=")
        # print(res)
        return res
  
   

