import urequests
import utime

def getServerStatus(ip, port=3055,path="/",trace=False):
    ln=f"[getServerStatus({path})]:"
    url = f"http://{ip}:{port}{path}"
    if trace:
        print(ln+f"Request to {url}...")
    
    try:
        # Робимо запит з таймаутом (щоб не зависнути назавжди)
        response = urequests.get(url, timeout=5)
        if trace:
            print(ln+"Response=")
            print(response)
        if response.status_code == 200:
            # Перетворюємо JSON-текст у словник Python
            data = response.json()
            if trace:
                print(ln+"data=")
                print(data)
            # Закриваємо з'єднання (критично для MicroPython, щоб не "текла" пам'ять)
            response.close()
            return data
        else:
            print(ln+f"Server error: {response.status_code}")
            response.close()
            return None
            
    except Exception as e:
        print(ln+f"Connection error: {e}")
        return None

# # --- Приклад використання ---
# server_ip = "192.168.1.130" # Тут може бути IP, знайдений через ваші UDP-запити
# status = getServerStatus(server_ip)

# if status is not None:
#     # Тепер ви можете звертатися до даних як до словника
#     # Якщо сервер прислав {"offGrid": "True"}, то:
#     print("Стан мережі:", status.get("offGrid"))
# else:
#     print("Не вдалося отримати статус.")