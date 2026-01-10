import uasyncio as asyncio


class HTTPServer:
    def __init__(self, port=80,trace=False):
        self.port = port
        self.trace=trace
        self.ln="[HTTP]::"
        self.ready=False

    async def _handle_request(self, reader, writer):
        
        # Читаємо тільки перший рядок запиту (напр. GET /status HTTP/1.1)
        request_line = await reader.readline()
        ln=""
        if self.trace:
            ln =self.ln+"_handle_request::\n"
            req = request_line.decode('utf-8').strip()
            print(ln + req)
        # Пропускаємо решту заголовків
        line=await reader.readline()    
        while line != b"\r\n":          
            if self.trace:
                print(line.decode('utf-8').strip())
            line = await reader.readline()
            pass
        
        request = str(request_line.decode())
        
        response=self.router(request)
        if self.trace:
            print(20*"-")
            print("response=",response)

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
