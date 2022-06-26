import socket
import threading
import cryptocode
import json


class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket): #инициализируем подклчюение
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("Новое подключение: ", clientAddress)

    def run(self):
        msg=''
        while True:
            data = self.csocket.recv(4096)
            msg = data.decode()
            msg = cryptocode.decrypt(msg, 'key')
            if msg == '' or msg == False: #проверка на пустое сообщение -> пользователь отключился
                print("Отключение")
                break
            if msg[0] == "L": #логин
                # Поиск данных в БД
                self.csocket.send(bytes("1", 'UTF-8'))
                pass
            elif msg[0] == "S": #регестраия, проврека на уникальный логин
                # Помещение данных в БД
                self.csocket.send(bytes("2", 'UTF-8'))
                pass
            elif msg[0] == "F": #поиск пользователя по бд
                users = ['oleg', 'nikitos'] #пример данных из БД по запросу
                # if не нашёл точно по имени но нашёл сопадения:
                #     data = json.dumps({"users": users})
                #     self.csocket.send(bytes("0", 'UTF-8'))
                #     self.csocket.send(data.encode())
                # elif нашёл точно по имени, открывается диалог:
                #     self.csocket.send(bytes("1", 'UTF-8'))
                pass
            elif msg[0] == "M": #Диалог с пользователем (запись в бд на сервере)
                print(msg)


if __name__ == '__main__':
    LOCALHOST = "127.0.0.1"
    PORT = 1337

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, PORT))
    print("Сервер запущен!")
    while True:
        server.listen(10) #слушаем одновременно 10 челиков
        clientsock, clentAddress = server.accept() #ждём нового подключения
        newthread = ClientThread(clentAddress, clientsock) # в новом потоке обрабатываем пользователя
        newthread.start()