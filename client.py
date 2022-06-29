import cryptocode
import socket
from threading import Thread
import threading
import json
import os.path
from datetime import datetime
import os
import time
len_field = 60#максиамльная длина строки в чате
half_len_field = int(len_field/2)#половина строки в чате


def commands():
    print("Для обновления переписки отправьте любое сообщение либо используйте команду /update")
    print("Для возврата назад и выбора другого пользователя напише /back")
    print("Для выхода из приложения используйте /exit")


def print_history():#печать истории диалога
    dialog = json.loads(client.recv(4096).decode())  # получаем историю
    print('Вы' + ' ' * (len_field - 2 - len(name_original)) + name_original)
    print("_" * len_field)
    for i in dialog.get('messages'):  # выводим её
        if i.get("author") == name_original:#вывод в правой части консоли пользователя с которым идёт переписка
            if len(i.get('massage')) < half_len_field:
                print(' ' * int(len_field - len(i.get('massage'))) + i.get('massage') + '\n')
            else: #если соообщение большое то разбиваем его на несколько строк
                numbers_n = float(len(i.get('massage')) / half_len_field)
                range_cycle = int(numbers_n)
                if numbers_n != int(numbers_n):
                    range_cycle = int(numbers_n) + 1
                for number in range(range_cycle):
                    if number == range_cycle and range_cycle == int(numbers_n):
                        print(' ' * int(len_field - len(i.get('massage'))) + i.get('massage') + '\n')
                    else:
                        print(" " * half_len_field + i.get('massage')[
                                                     number * half_len_field:(number + 1) * half_len_field])
        else: #вывод влевой части консоли залогиненого пользователя
            if len(i.get('massage')) < half_len_field:
                print(i.get('massage') + '\n')
            else:   #если соообщение большое то разбиваем его на несколько строк
                numbers_n = float(len(i.get('massage')) / half_len_field)
                range_cycle = int(numbers_n)
                if numbers_n != int(numbers_n):
                    range_cycle = int(numbers_n) + 1
                for number in range(range_cycle):
                    if number == range_cycle and range_cycle == int(numbers_n):
                        print(i.get('massage') + '\n')
                    else:
                        print(i.get('massage')[number * half_len_field:(number + 1) * half_len_field])


if __name__ == '__main__':
    clear_console = lambda: os.system('cls') #если очистка консоли не работает в ide, то включите эмуляцию терминала
                                                # run->Edit Configurations->Emulate terminal output
    SERVER = "127.0.0.1"
    PORT = 1337
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #открывание сокета, нужно будет сделать обёртку для TLS
    client.connect((SERVER, PORT))
    while True: #вход в ситему
        print("[1] Login\n[2]Sign in")
        res = input()
        clear_console()
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
                ans = client.recv(4096).decode() #ждём результат запроса
                if ans == '1':
                    clear_console()
                    print("Вы успшно вошли")
                    break
                elif ans == '-1':
                    clear_console()
                    print("Такой логин уже занят")
                elif ans == '-2':
                    clear_console()
                    print("Что то пошло не так, поробуйте снова")
                else:
                    clear_console()
                    print("Неверный логин или пароль")
                    continue
            else:
                clear_console()
                print("Введены неверные параметры, попробуйте снова")
        except:
            clear_console()
            print("Введены неверные параметры, попробуйте снова")

    print("Введите имя пользователя которому хотите написать:") #после логина ищем чубрика которому хотим написать
    while True: #Основное 'меню' чата
        name = input()
        name_original = name
        name = 'F' + name + " " + login
        name = cryptocode.encrypt(name, 'key') #шифруем и отпарвляем на сервер
        client.sendall(bytes(name, 'UTF-8'))

        ans = client.recv(4096).decode() #ждём овтета
        if ans == "0": #не смогли найти чела точно по имени
            ans = json.loads(client.recv(4096).decode()) #json файл со всеми челиками примерно сопадающими по имени
            if len(ans.get("users")) > 0: #если файл не пустой то печатаем этих пользователей и простим повторить попытку поиска
                print("Результаты по запросу " + name_original + ":")
                print(ans.get("users"))
            else: #если файл пустой то пользователей нет
                clear_console()
                print("Такого пользователя нет, попытайтесь ещё раз")
        elif ans == "1": #если нашли пользователя по имени
            clear_console()
            mode = client.recv(4096).decode()
            if mode == '1': #если есть история диалога
                print_history() #выводим историю
            print("Чтобы узнать команды отправьте /help")
            print("Введите сообщение:")
            while True: #начинаем диалог
                message = input()
                if message == '/help':
                    commands()
                    continue
                elif message == '/update':
                    client.sendall(bytes(cryptocode.encrypt("R" + login + " " + name_original, 'key'), 'UTF-8'))
                    mode = client.recv(4096).decode()
                    clear_console()
                    print_history()  # выводим обновлённый диалог
                    print("Введите сообщение:")
                    continue
                elif message == '/back':
                    clear_console()
                    print("Введите имя пользователя которому хотите написать:")
                    break
                elif message == '/exit':
                    print("Надеюсь ещё увидимся. До свидания)")
                    exit()

                info = "M" + login + " " + name_original
                info = cryptocode.encrypt(info, 'key')  # шифруем и отпарвляем на сервер
                client.sendall(bytes(info, 'UTF-8')) #отпаряем данные кто и кому
                client.sendall(bytes(message, 'UTF-8'))#отпарляем сообщение
                time.sleep(0.5)
                client.sendall(bytes(cryptocode.encrypt("R"+login+" "+name_original, 'key'), 'UTF-8'))#отпарялем запрос на обноваление диалога
                mode = client.recv(4096).decode() #ответ 1 - есть диалог 0 - диалог пустой
                if mode == "1":
                    clear_console()
                    print_history()#выводим обновлённый диалог
                    print("Введите сообщение:")
