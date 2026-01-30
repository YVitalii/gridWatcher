from setState import setState

state ={
    "offGrid":None,
    "T0":None,
    "T1":None,
    "time":None,
    "weekDay":None,
    "date":None,
    "heater":None,
    "heater":None,
    "taskT":{
        "min":6, 
        "mid":15, 
        "max":20
        },
    "taskMode":None,
    "masterServer":None,
    "httpServer":None,
    }

data={
    "offGrid":False,
    "T0":20.5,
    "T1":19.0,
    "taskT":{
        "min":11, 
        "mid":12, 
        "max":13
        }
    }


res=setState(data,state)
print("-"*30)
print("res=")

print(res)