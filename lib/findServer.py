import socket

def findServer(message=b"Hey GridWatcher!",port=5005):
    ln="[findServer]:"
    # Налаштування сокета
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.settimeout(3) # Чекаємо відповідь 3 секунди

    # message = b"DISCOVER_SERVER"
    # port = 5005

    print(ln+f"Looking for server:[{message}]")
    # Надсилаємо Broadcast на всю мережу
    client.sendto(message, ('192.168.1.255', port))

    try:
        data, addr = client.recvfrom(1024)
        data=data.decode()
        print("Response")
        print(data)
        print(addr)
        header=data.split(";")[0]#заголовок
        # rpartition повертає кортеж (перед, роздільник, після)
        _, _, port = data.rpartition("=")
        ip=addr[0]
        if header == "GridWatcher":
            
            return (ip,port)
    except OSError:  # MicroPython викине OSError при таймауті
        print(ln+"Timeout error")
        return None
    except Error as Err:
        print(ln+Err)
    finally:
        client.close()
        
    return None

if __name__ == "__main__":
    find_server()