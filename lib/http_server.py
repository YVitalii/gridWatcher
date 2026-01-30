import uasyncio as asyncio
from requestToDict import parseRequest

class HTTPServer:
    def __init__(self, port=80,trace=False):
        self.port = port
        self.trace=trace
        self.ln="[HTTP]::"
        self.ready=False

    async def _handle_request(self, reader, writer):
        ln = self.ln + "_handle_request::"
        request_line = ""
        request_firstLine= ""
        content_length = 0
        is_post = False       
        i = 0
        max_headers = 50
        while i<max_headers:
            try:
                raw_line= await reader.readline()
                # Якщо з'єднання закрите (EOF), повернеться b''
                if not raw_line:
                    if self.trace: print(f"{ln}EOF reached")
                    break
                line = raw_line.decode('utf-8')
                
                # 2. Якщо рядок порожній (тільки перенос) — кінець заголовків
                # Використовуємо strip(), щоб прибрати пробіли, \r та \n
                if line.strip() == "":
                    if self.trace: print(f"{ln}End of headers detected")
                    break

                # 1. Читаємо перший рядок (Method, Path, Proto)
                if i == 0:
                    request_line = line.strip()
                    is_post = line.startswith("POST")
        
    
                # 2. Якщо рядок порожній (\r\n), заголовки закінчилися
                if line == '\r\n' or line == '\n' or line=="":
                    break
                    
                # 3. Для POST витягуємо довжину тіла
                if is_post and line.lower().startswith("content-length:"):
                    content_length = int(line.split(':')[1].strip())
                    
                if self.trace:
                    print(f"{ln}header[{i}]::{line.strip()}")
                i += 1

            except Exception as e:
                if self.trace:
                    print(f"{ln}Error reading line: {e}")
                break

        # 4. Обробка тіла запиту для POST
        body = ""
        if is_post and content_length > 0:
            # Читаємо рівно стільки байтів, скільки вказано в Content-Length
            body_raw = await reader.read(content_length)
            body = body_raw.decode('utf-8')
            if self.trace:
                print(f"{ln}POST Body::{body}")

        # Фінальний результат для обробки
        full_request = request_line if not is_post else request_line + "\r\n" + body
        
        # Обробляємо тіло запиту, якщо є
      

        req= parseRequest(full_request)

        if self.trace:
            print(20*"-")
            print(ln+"parsed request:", str(req))
        

        response=self.router(req)

        if self.trace:
            print(20*"-")
            print(ln+"response=",response)

        await writer.awrite(response)
        await writer.wait_closed()

    async def start(self):
        
        # Запуск асинхронного сервера
        server=await asyncio.start_server(self._handle_request, "0.0.0.0", self.port)
        # print(f"[HTTP] Server listen on: {self.port}")
        self.ready=True
        await server.wait_closed()
    
    # must be defined in instance
    # should return response = tuple for writer.awrite(response)
    def router(self,req):
        return (req)
