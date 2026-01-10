from genFunc import toSeconds

class Manager ():
     
    def __init__(self, heater, accumulator,dT=1, minT=5, lowT=10, normT=15, highT=20, trace=False):
        self.heater = heater
        self.accumulator = accumulator
        self.dT=dT
        self.trace=trace
        self.ln="[Manager]::"

    def setHeater(self,currT,goalT):
        if currT < goalT :
            #  якщо температура нижче goalT, вмикаємо нагрівання
            self.heater.on()
        elif currT > goalT + self.dT:
            # при вищій температурі - все вимкнено
            self.heater.off()
    

    def test(offGrid=None,currT=None,clock=None,weekday=None):
        heater=self.heater
        accumulator = self.accumulator
        if (offGrid is None) or (currT is None) or (clock is None) or (weekday is None) :
            print(self.ln+"One of arguments are None, exit.")
            return
        # ------------ мережа відсутня 
        if (offGrid):
            accumulator.off()
            self.setHeater(currT,minT)

        # ------------ мережа є -----
        else: # offGrid=True -> onGrid
            # -------- working days -----------
            if (weekday<=4):

                #  --------- 00 - ніч -------------
                if (clock <= toSeconds("06:00:00")):
                    accumulator.on() if currT < self.highT else accumulator.off()
                    self.setHeater(currT,lowT)

                #  --------- розігрів до роботи -------------
                elif (clock <= toSeconds("08:00:00")):           
                    accumulator.on() if currT < self.highT else accumulator.off() # зазвичай не велике навантаження
                    self.setHeater(currT,normT)

                #  --------- робота до обіду -------------
                elif (clock <= toSeconds("11:55:00")):           
                    accumulator.off() # зазвичай велике навантаження
                    self.setHeater(currT,normT)

                #  --------- обід ------------- 
                elif (clock <= toSeconds("12:55:00")):                
                    accumulator.on() if currT < self.highT else accumulator.off() # зазвичай обід і навантаження немає
                    self.setHeater(currT,normT)

                #  --------- після обіду -------------
                elif (clock <= toSeconds("16:55:00")):
                    accumulator.off() # зазвичай велике навантаження
                    iself.setHeater(currT,normT)

                #  --------- після закінчення роботи до півночі -------------
                elif (clock <= toSeconds("23:59:59")):
                    accumulator.on() if currT < self.highT else accumulator.off()
                    self.setHeater(currT,lowT)
            else:
                # ----- вихідні дні ---------------
                accumulator.on() if currT < self.highT else accumulator.off()
                self.setHeater(currT,lowT)