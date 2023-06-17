import asyncio
import websockets
from websockets import WebSocketServerProtocol
import sys
import time

class Server:
    clients = set()

    async def register(self,ws:WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        print("Client %s connects" % (ws.remote_address,))

    async def unregister(self,ws:WebSocketServerProtocol) -> None:
        self.clients.remove(ws)
        print("Client %s disconnects" % (ws.remote_address,))

    def client_list(self, origin):
        list = []
        for client in self.clients:
            if client.remote_address != origin.remote_address:
                list.append(client)
        return list

    async def send_to_clients(self, message:str, origin:WebSocketServerProtocol) -> None:
        if self.client_list(origin):
            #await asyncio.wait([client.send(message) for client in self.clients])
            await asyncio.wait([client.send(message) for client in self.client_list(origin)]) #send to all except back the producer

    async def produce(self, message:str, ws: WebSocketServerProtocol) -> None:
        print("Sending %s in 5 seconds" % (message,))
        time.sleep(5)
        await ws.send(message)
        await ws.recv()

    async def ws_handler(self, ws: WebSocketServerProtocol, uri:str) -> None:
        await self.register(ws)
        try:
            await self.distribute(ws)
        finally:
            await self.unregister(ws)
    
    async def distribute(self, ws:WebSocketServerProtocol) -> None:
        async for message in ws:
            await self.send_to_clients(message, ws)

try:
    server = Server()
    start_server = websockets.serve(server.ws_handler,'0.0.0.0',8081)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()
except KeyboardInterrupt:
    print("Stopped server")
    sys.exit(0)


    