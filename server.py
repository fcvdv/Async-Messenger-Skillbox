import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            if decoded.startswith("login:"):
                if decoded not in self.server.logins:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(f"Hello, {self.login}.".encode())
                    self.server.logins.append(decoded)
                else:
                    self.transport.write("This login is already taken.".encode())
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.messages.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)

        for message in self.server.messages[:10]:
            self.transport.write(message.encode() + "\n".encode())

        print("Connected")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Connection lost")


class Server:
    clients: list
    logins: list
    messages: list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        print("Server launched ...")

        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888)

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server is stopped by hand")
