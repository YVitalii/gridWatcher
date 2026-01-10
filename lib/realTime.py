import ntptime
import time
import uasyncio as asyncio

class RealTime():

    def __init__(self,host=None):
        if host is None:
            ntptime.host = "ua.pool.ntp.org"
        self.ready=False
        self.ln="[realTime]"
    def getCurrTime(self):
        # return (year, month, monthDay, hour, minute, second, weekday, yearday)
        return time.gmtime(time.time() + 2*3600)

    
    def getTimeString(self):
        if not self.ready :
            return None
        (y,m,d,h,min,s,wd,yd) = self.getCurrTime()
        timeline = f'{h:02d}:{min:02d}:{s:02d}'
        return timeline
    #  ------------ perse date + time to "YYYY-MM-DD  HH:MM:SS" 
    def getDateString(self):
        if not self.ready :
            return None
        (y,m,d,h,min,s,wd,yd) = self.getCurrTime()
        timeline = f'{y}-{m:02d}-{d:02d}'
        return timeline
    def getDateTimeString(self):
        if not self.ready :
            return None
        return self.getDateString()+"T"+self.getTimeString()
    def getWeekDay(self):
        if not self.ready :
            return None
        weekday = self.getCurrTime()[6]
        days =("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
        return (weekday,days[weekday])

    async def start(self):
        try:
            while True:
                ntptime.settime()# Synchronise the system time using NTP
                self.ready=True
                await asyncio.sleep(60*60) # оновлюємо кожну годину
        except Exception as e:
            self.ready=False
            print(self.ln+"Error of synchronisation:", e)
            await asyncio.sleep(10) # кожні 10 сек


    
    