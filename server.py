import socket
import sqlite3
import threading
import cryptocode
import json
from datetime import datetime
import os.path
import os
import time
import shutil
import rsa
import pickle


class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):  # инициализируем подклчюение
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.public_key, self.privat_key = rsa.newkeys(512)
        self.public_key_from_user = None
        print("Новое подключение: ", clientAddress)

    def check_unique(self, login): #функция првоерки на уникалдьный логин
        try:
            sqlite_connection = sqlite3.connect('resources/sqlite_python.db') #получаем даныне с бд
            cursor = sqlite_connection.cursor()
            cursor.execute('SELECT * FROM users')
            data = cursor.fetchall()
            cursor.close()
        except:
            if sqlite_connection:
                cursor.close()
            return -1
        for i in data: #проверяем есть ли такой же логин
            if i[1] == login:
                return 0
        return 1

    def send_encode_msg(self, text, public_key):
        self.csocket.sendall(rsa.encrypt(text.encode(), public_key))

    def run(self):
        msg = ''
        key = pickle.dumps(self.public_key)
        self.csocket.send(key)
        self.public_key_from_user = pickle.loads(self.csocket.recv(4096))
        while True:
            try:
                data = self.csocket.recv(4096)  # получение сообщений от пользователя
                msg = rsa.decrypt(data, self.privat_key).decode() #расшифровка сообщений
            except:
                print("Отключение")
                break
            if msg == '' or msg == False:  # проверка на пустое сообщение -> пользователь отключился
                print("Отключение")
                break
            if msg[0] == "L":  # логин
                #парс полученный строки с данными
                login = msg[1:msg.find(" ")]
                password = msg[msg.find(" ") + 1:]
                # Поиск данных в БД
                try:
                    sqlite_connection = sqlite3.connect('resources/sqlite_python.db')
                    cursor = sqlite_connection.cursor()
                    cursor.execute('SELECT * FROM users WHERE login=?', (login,))
                    data = cursor.fetchall()
                    cursor.close()
                    if data[0][2] == password: #проверка пароля по бд
                        self.send_encode_msg("1", self.public_key_from_user)
                    else:
                        self.send_encode_msg("0", self.public_key_from_user)
                except:
                    self.send_encode_msg("-2", self.public_key_from_user)
                    if sqlite_connection:
                        cursor.close()
            elif msg[0] == "S":  # регестраия, проврека на уникальный логин
                # Получение данных из сообщения
                login = msg[1:msg.find(" ")]
                password = msg[msg.find(" ") + 1:]
                if self.check_unique(login) == 0: #проверка на уникальный логин
                    self.send_encode_msg("-1", self.public_key_from_user)
                    continue
                if self.check_unique(login) == -1:
                    self.send_encode_msg("-2", self.public_key_from_user)
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
                    self.send_encode_msg("1", self.public_key_from_user)
                except:
                    self.send_encode_msg("-2", self.public_key_from_user)
                    if sqlite_connection:
                        cursor.close()

            elif msg[0] == "F":
                #парс строки с данными от пользователя
                name = msg[1:msg.find(" ")]
                login = msg[msg.find(" ") + 1:]
                sqlite_connection = sqlite3.connect('resources/sqlite_python.db') # получение всех пользователей
                cursor = sqlite_connection.cursor()
                cursor.execute('SELECT login FROM users')
                data = cursor.fetchall()
                cursor.close()

                users = []
                flag = True
                for i in data:      # поиск пользователя по бд
                    if i[0] == name:
                        self.send_encode_msg("1", self.public_key_from_user)
                        flag = False
                        if os.path.isfile(f'repo/{login}/{name}.json'): #если есть диалог с этим пользователем отправляем его
                            time.sleep(0.5) #задержка перед отправкой данных, чтобы они не слипались
                            self.send_encode_msg("1", self.public_key_from_user)
                            time.sleep(0.5)
                            with open(f'repo/{login}/{name}.json', "r", encoding='utf8') as file:
                                load = json.load(file)
                            self.csocket.send(json.dumps({"messages": load}).encode())
                        else:
                            self.send_encode_msg("0", self.public_key_from_user)
                            # load = []
                            # self.csocket.send(json.dumps({"messages": load}).encode())
                        break
                    if i[0].find(name) != -1:#если не нашли точно по имени, то добавляем пользователей которые схожи с запросом
                        flag = True          #и отпраляем пользователю
                        users.append(i[0])
                if flag:
                    self.send_encode_msg("0", self.public_key_from_user)
                    self.csocket.send(json.dumps({"users": users}).encode())
            elif msg[0] == "M":  # Диалог с пользователем (запись в бд на сервере)
                #парсим сообщение от пользователя
                from_user = msg[1:msg.find(" ")] #от кого
                to_user = msg[msg.find(" ") + 1:]#кому
                massage = rsa.decrypt(self.csocket.recv(4096), self.privat_key).decode()#само сообщение

                if os.path.isfile(f'repo/{from_user}/{to_user}.json'):  # если диалог уже есть записываем данные
                    ###################################### для отправителя
                    data = {
                            'author':from_user,
                            'massage': massage,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}
                    with open(f'repo/{from_user}/{to_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                    load.append(data)
                    with open(f'repo/{from_user}/{to_user}.json', 'w', encoding='utf8') as f:
                        json.dump(load, f, indent=4, ensure_ascii=False)
                    ###################################### для того кто получает
                    data = {
                            'author': from_user,
                            'massage': massage,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}
                    with open(f'repo/{to_user}/{from_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                    load.append(data)
                    with open(f'repo/{to_user}/{from_user}.json', 'w', encoding='utf8') as f:
                        json.dump(load, f, indent=4, ensure_ascii=False)
                else:  # если диаолога ещё не было, то создаём файлы для записи и записываем
                    if not os.path.exists(f'repo/{from_user}'):
                        os.mkdir(f'repo/{from_user}')
                    if not os.path.exists(f'repo/{to_user}'):
                        os.mkdir(f'repo/{to_user}')
                    ###################################### для отправителя
                    data = [{
                            'author': from_user,
                             'massage': massage,
                             'data': datetime.now().strftime("%H:%M %d/%m/%Y")}]
                    with open(f'repo/{from_user}/{to_user}.json', 'w', encoding='utf8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    ###################################### для того кто получает
                    data = [{
                            'author': from_user,
                             'massage': massage,
                             'data': datetime.now().strftime("%H:%M %d/%m/%Y")}]
                    with open(f'repo/{to_user}/{from_user}.json', 'w', encoding='utf8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            elif msg[0] == 'R':
                login = msg[1:msg.find(" ")] #от кого
                name = msg[msg.find(" ") + 1:]#кому
                if os.path.isfile(f'repo/{login}/{name}.json'):  # если есть диалог с этим пользователем отправляем его
                    self.send_encode_msg("1", self.public_key_from_user)
                    time.sleep(0.5)                             # задержка перед отправкой данных, чтобы они не слипались
                    with open(f'repo/{login}/{name}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                    self.csocket.send(json.dumps({"messages": load}).encode())
                else:
                    self.send_encode_msg("0", self.public_key_from_user)
            elif msg[0] == 'U':
                from_user = msg[1:msg.find(" ")]  # от кого
                to_user = msg[msg.find(" ") + 1:]  # кому
                name_file = rsa.decrypt(self.csocket.recv(4096), self.privat_key).decode()  # название файла
                if os.path.isfile(f'repo/{from_user}/{to_user}.json'):  # если диалог уже есть записываем данные
                    ###################################### для отправителя
                    mode = 1
                    with open(f'repo/{from_user}/{to_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                        for i in load:
                            if i.get('massage') == name_file:
                                self.send_encode_msg("0", self.public_key_from_user)
                                mode = 0
                        if mode == 1:
                            self.send_encode_msg("1", self.public_key_from_user)
                    data = {
                            'author':from_user,
                            'massage': name_file,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}
                    with open(f'repo/{from_user}/{to_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                    load.append(data)
                    with open(f'repo/{from_user}/{to_user}.json', 'w', encoding='utf8') as f:
                        json.dump(load, f, indent=4, ensure_ascii=False)
                    ###################################### для того кто получает
                    data = {
                            'author': from_user,
                            'massage': name_file,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}
                    with open(f'repo/{to_user}/{from_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                    load.append(data)
                    with open(f'repo/{to_user}/{from_user}.json', 'w', encoding='utf8') as f:
                        json.dump(load, f, indent=4, ensure_ascii=False)
                else:
                    if not os.path.exists(f'repo/{from_user}'):
                        os.mkdir(f'repo/{from_user}')
                        ###################################### для отправителя
                        data = [{
                            'author': from_user,
                            'massage': name_file,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}]
                        with open(f'repo/{from_user}/{to_user}.json', 'w', encoding='utf8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                    if not os.path.exists(f'repo/{to_user}'):
                        os.mkdir(f'repo/{to_user}')
                        ###################################### для того кто получает
                        data = [{
                            'author': from_user,
                            'massage': name_file,
                            'data': datetime.now().strftime("%H:%M %d/%m/%Y")}]
                        with open(f'repo/{to_user}/{from_user}.json', 'w', encoding='utf8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)

                size = rsa.decrypt(self.csocket.recv(4096), self.privat_key).decode()  # расшифровка сообщений
                count = 0
                with open(f'repo/{from_user}/' + name_file, 'wb') as f:
                    while True:
                        b = self.csocket.recv(1024)
                        f.write(b)
                        count += 1
                        if not b:
                            break
                        if count == int(size):
                            break
                create_file = open(f'repo/{to_user}/' + name_file, 'w')
                create_file.write('')
                create_file.close()
                shutil.copy(f'repo/{from_user}/' + name_file, f'repo/{to_user}/' + name_file)
            elif msg[0] == 'D':
                from_user = msg[1:msg.find(" ")]  # от кого
                to_user = msg[msg.find(" ") + 1:]  # кому
                name_file = rsa.decrypt(self.csocket.recv(4096), self.privat_key).decode()  # название файла
                mode = 1
                if os.path.isfile(f'repo/{from_user}/{to_user}.json'):
                    with open(f'repo/{from_user}/{to_user}.json', "r", encoding='utf8') as file:
                        load = json.load(file)
                        for i in load:
                            if i.get('massage') == name_file:
                                self.send_encode_msg("1", self.public_key_from_user)
                                mode = 0
                                break
                        if mode == 1:
                            self.send_encode_msg("0", self.public_key_from_user)
                            continue
                else:
                    self.send_encode_msg("1", self.public_key_from_user)
                    continue
                time.sleep(0.5)
                file_stats = os.stat(f'repo/{to_user}/' + name_file).st_size/1024
                if file_stats != int(file_stats):
                    file_stats = int(file_stats)+1
                self.send_encode_msg(f'{file_stats}', self.public_key_from_user)
                time.sleep(0.5)
                f = open(f'repo/{to_user}/' + name_file, 'rb')
                l = f.read(1024)
                while (l):
                    # отправляем файл на клиент
                    self.csocket.send(l)
                    l = f.read(1024)
                f.close()


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
        newthread.start() #запускаем поток
