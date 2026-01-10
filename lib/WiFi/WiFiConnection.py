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
            return
        # print("========")
        
        # print(self.ssid)
        # print("========")
        self._pwd = self.networks[self.ssid]
        if trace:
            print("Selected network: {}; pwd: {}; {}dB".format(self.ssid,self._pwd,self.strength))
        self.wlan.connect(self.ssid, self._pwd)
        counter = 10
        print(ln+"Connecting")
        while not self.wlan.isconnected():
            self.connecting(self,counter)        
            counter = counter - 1
            if counter == 0:
                print("Not connected after 10 times.Reboot...")
                await asyncio.sleep(2)
                reset()
            await asyncio.sleep(1)
        self.ip = self.wlan.ipconfig('addr4')[0]
        # print(ln+"self.ip=")
        # print(self.ip)
        self.connected(self)


    async def start(self,trace=False):
        ln =self.ln+"start()::"
        if trace:
            print(ln+"Started")
        while True:
            if not self.isconnected():
                print(ln+"Connection lost reconecting.." )
                self.disconnected(self)
                await self.connect()
            if trace :
                print(ln+"Connection Ok" )
            await asyncio.sleep(5)
  
    def isconnected(self):
        res=self.wlan.isconnected() and self.wlan.status() == network.STAT_GOT_IP
        # print(self.ln+"isconnected()::res=")
        # print(res)
        return res
  
   

