import socket
import sqlite3
import threading
import cryptocode
import json
from datetime import datetime


class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):  # инициализируем подклчюение
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print("Новое подключение: ", clientAddress)

    def check_unique(self, login):
        try:
            sqlite_connection = sqlite3.connect('resources/sqlite_python.db')
            cursor = sqlite_connection.cursor()
            cursor.execute('SELECT * FROM users')
            data = cursor.fetchall()
            cursor.close()
        except:
            if sqlite_connection:
                cursor.close()
            return -1
        for i in data:
            if i[1] == login:
                return 0
        return 1

    def run(self):
        msg = ''
        while True:
            data = self.csocket.recv(4096)
            msg = data.decode()
            msg = cryptocode.decrypt(msg, 'key')
            if msg == '' or msg == False:  # проверка на пустое сообщение -> пользователь отключился
                print("Отключение")
                break
            if msg[0] == "L":  # логин
                # Поиск данных в БД
                login = msg[1:msg.find(" ")]
                password = msg[msg.find(" ") + 1:]
                try:
                    sqlite_connection = sqlite3.connect('resources/sqlite_python.db')
                    cursor = sqlite_connection.cursor()
                    cursor.execute('SELECT * FROM users WHERE login=?', (login,))
                    data = cursor.fetchall()
                    cursor.close()
                    if data[0][2] == password:
                        self.csocket.send(bytes("1", 'UTF-8'))
                    else:
                        self.csocket.send(bytes("0", 'UTF-8'))
                except:
                    self.csocket.send(bytes("-2", 'UTF-8'))
                    if sqlite_connection:
                        cursor.close()
            elif msg[0] == "S":  # регестраия, проврека на уникальный логин
                # Получение данных из сообщения
                login = msg[1:msg.find(" ")]
                password = msg[msg.find(" ") + 1:]
                if self.check_unique(login) == 0: #проверка на уникальный логин
                    self.csocket.send(bytes("-1", 'UTF-8'))
                    continue
                if self.check_unique(login) == -1:
                    self.csocket.send(bytes("-2", 'UTF-8'))
                    continue
                # Помещение данных в БД
                try:
                    sqlite_connection = sqlite3.connect('resources/sqlite_python.db')
                    cursor = sqlite_connection.cursor()
                    insert_with_param = """INSERT INTO users
                                                  (login, password, date)
                                                  VALUES (?, ?, ?);"""
                    now = datetime.now().strftime("%d/%m/%Y")
                    data_tuple = (login, password, now)
                    cursor.execute(insert_with_param, data_tuple)
                    sqlite_connection.commit()
                    cursor.close()
                    self.csocket.send(bytes("1", 'UTF-8'))
                except:
                    self.csocket.send(bytes("-2", 'UTF-8'))
                    if sqlite_connection:
                        cursor.close()

            elif msg[0] == "F":  # поиск пользователя по бд
                name = msg[1:]
                sqlite_connection = sqlite3.connect('resources/sqlite_python.db') # получение всех пользователей
                cursor = sqlite_connection.cursor()
                cursor.execute('SELECT login FROM users')
                data = cursor.fetchall()
                cursor.close()
                users = []
                flag = True
                for i in data:
                    if i[0] == name:
                        self.csocket.send(bytes("1", 'UTF-8'))
                        flag = False
                        break
                    if i[0].find(name) != -1:
                        flag = True
                        users.append(i[0])
                if flag:
                    self.csocket.send(bytes("0", 'UTF-8'))
                    self.csocket.send(json.dumps({"users": users}).encode())
            elif msg[0] == "M":  # Диалог с пользователем (запись в бд на сервере)
                name = msg[1:msg.find(" ")]
                massage = msg[msg.find(" ") + 1:]


if __name__ == '__main__':
    LOCALHOST = "127.0.0.1"
    PORT = 1337

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCALHOST, PORT))
    print("Сервер запущен!")
    while True:
        server.listen(10)  # слушаем одновременно 10 челиков
        clientsock, clentAddress = server.accept()  # ждём нового подключения
        newthread = ClientThread(clentAddress, clientsock)  # в новом потоке обрабатываем пользователя
        newthread.start()
