import ujson

def parseRequest(req):
    ln="lib/requestToDict.py::parseRequest()::"
    trace=1
    if trace: print(f"{ln}DEBUG: req=[ '{req}' ]")
    try:
        firstHeader=req.split('\n')[0]
        if trace: print(f"{ln}DEBUG: firstHeader=[ '{firstHeader}' ]")
        if firstHeader.startswith('GET'):
            if trace: print(f"{ln}DEBUG: Detected GET request.")
            return parseGetRequest(firstHeader)
        elif firstHeader.startswith('POST'):
            if trace: print(f"{ln}DEBUG: Detected POST request.")
            return parsePostRequest(req)
    except Exception as e:
        if trace: print(f"{ln}ERROR: Exception occurred: {str(e)}")
        return {
            'method': None,
            'path': None,
            'data': {},
            'error': str(e)
        }
 
def parseGetRequest(req_line):
    # Вхід: 'GET /set?taskTmax=30&taskTmid=20 HTTP/1.1'
    res = {
        'method': 'GET',
        'path': '',
        'data': {},
        'error': None
    }
    
    try:
        # 1. Розбиваємо рядок по пробілах: [Метод, Шлях+Параметри, Протокол]
        parts = req_line.split(' ')
        if len(parts) < 2:
            res['error'] = "Invalid HTTP line"
            return res
            
        full_path = parts[1] # Результат: "/set?taskTmax=30&taskTmid=20"
        
        # 2. Відділяємо шлях від параметрів
        path_parts = full_path.split('?')
        res['path'] = path_parts[0] # Результат: "/set"
        
        # 3. Якщо є знак '?', обробляємо параметри
        if len(path_parts) > 1:
            query_string = path_parts[1]
            params = query_string.split('&') # Розділяємо пари: ['taskTmax=30', 'taskTmid=20']
            
            for p in params:
                if '=' in p:
                    kv = p.split('=')
                    key = kv[0]
                    value = kv[1] if len(kv) > 1 else ''
                    
                    # Спроба конвертації типів (для зручності в основному коді)
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass # Залишаємо як рядок, якщо не число
                        
                    res['data'][key] = value
                    
    except Exception as e:
        res['error'] = f"Parse error: {str(e)}"
        
    return res


def parsePostRequest(req):
    ln="lib/requestToDict.py::parsePostRequest()::"
    trace=1
    if trace: print(f"{ ln}DEBUG: req=[ '{req}' ]")
    res = {
        'method': 'POST',
        'path': req.split('\r\n')[0].split(' ')[1].strip(),
        'data': {},
        'error': None
    }
    try:
        bodyString=req.split('\r\n')[1].strip()
        if trace: print(f"{ ln}DEBUG: bodyString={bodyString}")
        # params=bodyString.replace('{','').replace('}','').split(',')
        res["data"]=ujson.loads(bodyString)
        if trace: print(f"{ ln}DEBUG: res['data']={res['data']}")
        return res
    except (IndexError, ValueError):    
        print(f"{ln}::ERROR: No body string found in the request={req}")
        return {}
