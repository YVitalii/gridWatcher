import uasyncio as asyncio
from machine import Pin

class ContactSensor:
    def __init__(self, pin_id, name="Sensor"):
        # Налаштовуємо пін з підтяжкою до живлення
        self.pin = Pin(pin_id, Pin.IN, Pin.PULL_UP)
        self.name = name
        self.state = self.pin.value()  # Поточний стан (1 - OFF, 0 - ON)
        self.is_on = self.state == 0
        
    async def monitor(self, callback=None):
        """Cycle of state monitoring"""
        print(f"[{self.name}] monitoring started on  {self.pin}")
        
        while True:
            current_val = self.pin.value()
            
            # Якщо стан змінився
            if current_val != self.state:
                # Чекаємо 50мс для виключення брязкоту контактів
                await asyncio.sleep_ms(50)
                
                # Перевіряємо ще раз після паузи
                if self.pin.value() == current_val:
                    self.state = current_val
                    self.is_on = (current_val == 0)
                    
                    # status_str = "ON" if self.is_on else "OFF"
                    # print(f"[{self.name}] State changed: {status_str}")
                    
                    # Якщо передана функція-коллбек, викликаємо її
                    if callback:
                        callback(self.is_on)
            
            # Поступаємося часом іншим задачам (HTTP/UDP серверам)
            await asyncio.sleep_ms(100)