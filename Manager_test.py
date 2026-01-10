from Manager import Manager

class PinEmulator():
    
    def __init__(self,number):
        self.curVal=0
        self.number=number

    def value(self,v=None):
        if (v is None):
            return self.curVal
        if v == 0:
            self.curVal=0
        else:
            self.curVal=1
        return self.curVal
    
    def on(self):
        self.value(1)
        return self.value()
    def off(self):
        self.value(0)
        return self.value()

def printMsg(res):
    msg=""
    for i in range(0,len(res)):
        msg += f"{res[i]:<10}"
    print(msg)

def printHead():
    print(f"{"weekday":<10}{"clock":<10}{"tT":<10}{"currT":<10}{"heater":<10}{"accumulator":<10}")

manager=Manager(
    heater=PinEmulator(11),
    accumulator=PinEmulator(12),
    dT=1,
    minT=6,
    lowT=10,
    normT=15,
    highT=18,
    trace=True
    )

printHead()
for day in (0,4,6):
    print (f"====== {'Working' if day <=4 else "Freeday"} =========")
    for offGrid in range(0,2):
        print(f"====== offGrid={offGrid} =======")
        for hours in (
            "00:50:00",
            "05:55:00",
            "06:30:00",
            "07:30:00",
            "08:30:00",
            "11:30:00",
            "12:00:00",
            "13:00:00",
            "16:00:00",
            "17:00:00",
            "22:00:00"
            ):
            for temp in (0,4,11,17,21):
                printMsg(manager.test(
                    offGrid=offGrid,
                    currT=temp,
                    clockStr=hours,
                    weekday=day))
             
