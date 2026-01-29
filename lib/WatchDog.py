from machine import WDT
import uasyncio as asyncio

# Створюємо WDT з таймаутом 8 секунд
wdt = WDT(timeout=10000)

async def start(trace=False):
    while True:
        # "Годуємо" пса. Якщо код зависне і цей рядок не виконається 8 сек — 
        # плата перезавантажиться автоматично на рівні заліза.
        wdt.feed() 
        if trace:
            print("WatchDog was reset")
        await asyncio.sleep(5)
