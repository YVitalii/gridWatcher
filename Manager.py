from genFunc import toSeconds

class Manager():
    def __init__(
        self, 
        heater=None, 
        accumulator=None, 
        dT=1, 
        minT=5, 
        lowT=10, 
        normT=15, 
        highT=17, 
        trace=False):
        
        self.trace=trace
        self.ln="[Manager]::"
        self.heater = heater
        self.accumulator = accumulator
        self.dT=dT
        self.minT=minT
        self.lowT=lowT
        self.normT=normT
        self.highT=highT
        self.state=None

    def setHeater(self,currT,goalT):
        if currT < goalT :
            #  якщо температура нижче goalT, вмикаємо нагрівання
            self.heater.on()
        elif currT > goalT + self.dT:
            # при вищій температурі - все вимкнено
            self.heater.off()
    

    def test(self,offGrid=None,currT=None,clockStr=None,weekday=None):
        heater=self.heater
        accumulator = self.accumulator
        clock=toSeconds(clockStr)
        msg=""
        if (offGrid is None) or (currT is None) or (clockStr is None) or (weekday is None) :
            print(self.ln+"One of arguments are None, exit.")
            return
        # ------------ мережа відсутня 
        if (offGrid):
            accumulator.off()
            self.setHeater(currT,self.minT)
            tT =self.minT
            msg="GridOff->"
        # ------------ мережа є -----
        else: # offGrid=True -> onGrid
            msg="GridOn->"
            # -------- working days -----------
            if (weekday<=4):

                #  --------- 00 - ніч -------------
                if (clock <= toSeconds("06:00:00")):
                    accumulator.on() if currT < self.highT else accumulator.off()
                    self.setHeater(currT,self.lowT)
                    tT =self.lowT


                #  --------- розігрів до роботи -------------
                elif (clock <= toSeconds("08:00:00")):           
                    accumulator.on() if currT < self.highT else accumulator.off() # зазвичай не велике навантаження
                    self.setHeater(currT,self.normT)
                    tT =self.normT


                #  --------- робота до обіду -------------
                elif (clock <= toSeconds("11:55:00")):           
                    accumulator.off() # зазвичай велике навантаження
                    self.setHeater(currT,self.normT)
                    tT =self.normT


                #  --------- обід ------------- 
                elif (clock <= toSeconds("12:55:00")):                
                    accumulator.on() if currT < self.highT else accumulator.off() # зазвичай обід і навантаження немає
                    self.setHeater(currT,self.normT)
                    tT =self.normT


                #  --------- після обіду -------------
                elif (clock <= toSeconds("16:55:00")):
                    accumulator.off() # зазвичай велике навантаження
                    self.setHeater(currT,self.normT)
                    tT =self.normT

                #  --------- після закінчення роботи до півночі -------------
                elif (clock <= toSeconds("23:59:59")):
                    accumulator.on() if currT < self.highT else accumulator.off()
                    self.setHeater(currT,self.lowT)
                    tT =self.lowT
            else:
                # ----- вихідні дні ---------------
                tT =self.lowT
                accumulator.on() if currT < self.highT else accumulator.off()
                self.setHeater(currT,self.lowT)
                
        # if self.trace:
        #     msg=f"{weekday}\t{clockStr}\t{currT}\t{heater.value()}\t{accumulator.value()}"
        #     print(msg)
        self.state=(weekday,clockStr,tT,currT,heater.value(),accumulator.value())
        return  self.state