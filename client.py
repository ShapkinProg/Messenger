import cryptocode
import socket
from threading import Thread
import threading
import json


if __name__ == '__main__':
    SERVER = "127.0.0.1"
    PORT = 1337

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #открывание сокета, нужно будет сделать обёртку для TLS
    client.connect((SERVER, PORT))

    while True:
        print("[1] Login\n[2]Sign in")
        res = input()
        try:
            if int(res) == 1 or int(res) == 2:
                print("Введите ваш логин:")
                login = input()
                print("Введите ваш пароль:")
                password = input()
                if int(res) == 1: #логин
                    send_login = "L" + login + " " + password
                elif int(res) == 2: #регестрация
                    send_login = "S" + login + " " + password
                send_login = cryptocode.encrypt(send_login, 'key') #на всякий случай шифрование перед отправкой
                client.sendall(bytes(send_login, 'UTF-8'))
                ans = client.recv(4096) #ждём результат запроса
                if ans == '1':
                    print("Вы успшно вошли")
                    break
                elif ans == '-1':
                    print("Такой логин уже занят")
                else:
                    print("Неверный логин или пароль")
                    continue
            else:
                print("Введены неверные параметры, попробуйте снова")
        except:
            print("Введены неверные параметры, попробуйте снова")

    print("Введите имя пользователя которому хотите написать:") #после логина ищем чубрика которому хотим написать
    while True:
        name = input()
        name_original = name
        name = 'F' + name
        name = cryptocode.encrypt(name, 'key') #шифруем и отпарвляем на сервер
        client.sendall(bytes(name, 'UTF-8'))
        ans = client.recv(4096) #ждём овтета
        if ans == "0": #не смогли найти чела точно по имени
            ans = json.loads(ans.decode()) #json файл со всеми челиками примерно сопадающими по имени
            if len(ans.get("users")) > 0: #если файл не пустой то печатаем этих пользователей и простим повторить попытку поиска
                print("Результаты по запросу " + name_original + ":")
                print(ans.get("users"))
            else: #если файл пустой то пользователей нет
                print("Такого пользователя нет, попытайтесь ещё раз")
        elif ans == "1": #если нашли пользователя по имени
            print("Введите сообщение:")
            while True: #начинаем диалог
                message = input()
                message = "M" + " " + name + message
                client.sendall(bytes(message, 'UTF-8'))
