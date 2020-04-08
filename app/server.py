#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if len(self.server.get_clients_by_login(self.login)) == 1:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой.\n".encode()
                    )
                    self.transport.close()
            else:
                self.transport.write("Неправильный логин\n".encode())
        #print("Список клиентов:")
        #self.server.print_clients()

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")
        #print("Список клиентов: ")
        #self.server.print_clients()

    def send_history(self):
        history_ = self.server.get_history()
        for msg in history_:
            self.transport.write(msg.encode())

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    def print_clients(self):
        for cl in self.clients:
            print(cl.login)

    def get_clients_by_login(self, login):
        clients_ = []
        for client in self.clients:
            if client.login == login:
                clients_.append(client)
        return clients_

    def get_client_by_login(self, login):
        for client in self.clients:
            if client.login == login:
                return client
        return None

    def get_count_of_login(self, login):
        cnt = 0
        for client in self.clients:
            if client.login == login:
                cnt = cnt + 1
        return cnt

    def get_history(self, n_last_messages = 10):
        if len(self.history) > n_last_messages:
            return self.history[len(self.history) - n_last_messages:]
        return self.history

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
