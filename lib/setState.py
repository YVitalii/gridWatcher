
def setState(data,state):
    ln="main::[setState]:"
    trace=False
    if trace:
        print(ln+f"data={data}, state={state}")
    body={} 
    if isinstance(data,dict) and isinstance(state,dict):       
        for key in data:
            if isinstance(data[key], dict):
                # рекурсивний виклик для вкладених словників
                if trace:
                    print(ln+f"Recursion for key={key}")
                body[key] = setState(data[key], state[key])
                continue
            if not key in state:
                body[key]=f"Error: key '{key}' not present in state"
                if trace:
                    print(ln+body[key])
                continue
            try:
                if isinstance(data[key],type(state[key])) or state[key] is None:
                    state[key]=data[key]
                    body[key]=data[key]
                    if trace:
                        print(ln+f"Set state[{key}]={data[key]}")
                else:
                    body[key]=f"Error: type mismatch {type(data[key])}!={type(state[key])}"
                    if trace:
                        print(ln+body[key])
            except Exception as e:
                body[key]=ln+f"Error setting state[{key}]={data[key]}: {e}"
    else:
        body={"error":f"Error: type mismatch {type(data)}!={type(state)}"}
    return body