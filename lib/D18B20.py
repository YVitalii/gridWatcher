import machine
import onewire
import ds18x20
import uasyncio as asyncio
from micropython import const

T_HYST = 0.5 

class TemperatureSensor:
    
    def __init__(self, pin_id=15,interval=10000,tHysteresis=0.5,trace=False):
        # Ініціалізація шини OneWire на піні D15
        self.ow = onewire.OneWire(machine.Pin(pin_id))
        self.ds = ds18x20.DS18X20(self.ow)
        self.ln = "[D18B20]:"
        self.trace=trace
        self.interval = interval
        self.tHysteresis=tHysteresis
        # Пошук датчиків на шині
        self.roms = self.ds.scan()
        print( self.ln+"Devices=")
        print(self.roms)
        if not self.roms:
            print(this.ln+"Sensor DS18B20 not found!")
            machine.reset()

        
        self.last_temp = 0  # Сховище для останнього значення
        self.trace=trace

    async def start(self):
        """Внутрішній цикл періодичного опитування"""
        # print(self.ln+"_update_loop::Started")
        while True:
            if self.roms:
                try:
                    # Подаємо команду на старт вимірювання
                    self.ds.convert_temp()
                    if self.trace:
                        print(self.ln+"Start conversion")
                    # Чекаємо завершення конвертації (мін. 750мс для 12-біт)
                    await asyncio.sleep_ms(750)
                    
                    # Зчитуємо дані з першого знайденого датчика
                    temp = self.ds.read_temp(self.roms[0])
                                 
                    # Перевіряємо на коректність (DS18B20 іноді повертає 85.0 при помилці)
                    if temp != 85.0:
                        temp = round(temp, 1)
                        dT=abs(self.last_temp - temp)
                        if self.trace:
                            print(self.ln+f"Was reading: temp={temp}; last_temp={self.last_temp}; dT={dT}")
                             
                              
                        if dT > self.tHysteresis:
                            self.last_temp = temp
                    if (self.trace):
                        print(self.ln+f"self.last_temp={self.last_temp}")
                except Exception as e:
                    print(self.ln+f"Error of reading: {e}")
            
            # Чекаємо до наступного циклу опитування (10 сек мінус час конвертації)
            await asyncio.sleep_ms(self.interval - 750)

    def getT(self):
        """Повертає останню зчитану температуру або 30C якщо ще не прочитана"""
        return 30 if (self.last_temp is None) else self.last_temp

  
# --- Приклад використання ---
async def main():
    sensor = TemperatureSensor(15)
    sensor.start()  # Запускаємо фонове опитування
    
    while True:
        current_t = sensor.getT()
        if current_t is not None:
            print(f"Current T=: {current_t} °C")
        else:
            print(this.ln+"Waiting for the First reading...")
            
        await asyncio.sleep(2) # Виводимо значення кожні 2 секунди

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Зупинено")