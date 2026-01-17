import uasyncio as asyncio
import gc

def getInfo():
    free = gc.mem_free()      # Вільна пам'ять у байтах
    allocated = gc.mem_alloc() # Використана пам'ять у байтах
    total = free + allocated   # Загальний обсяг купи
    ln="[RAM]::"
    print(f"{ln} Used: {allocated / 1024:.2f} kB ({(allocated/total*100):.1f}%)")
    # print(f"{ln} Free: {free / 1024:.2f} kB")
    # print(f"{ln} Total space: {total / 1024:.2f} kB")


