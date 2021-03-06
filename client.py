import ssl
import socket
import json
import os.path
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import rsa
import pickle
len_field = 60#максиамльная длина строки в чате
half_len_field = int(len_field/2)#половина строки в чате
wrong_parameters = "Введены неверные параметры, попробуйте снова"
input_message = "Введите сообщение:"

def send_encode_msg(text, public_key):
    client.sendall(rsa.encrypt(text.encode(), public_key))


def commands():
    print("Если вы хотите посомтреть всю историю переписки используйте команду /all")
    print("Для отправки файла отправьте команду /upload")
    print("Для получения файла отправьте команду /download + точное название файла с его расширением(example.txt)")
    print("Для обновления переписки отправьте любое сообщение либо используйте команду /update")
    print("Для возврата назад и выбора другого пользователя напише /back")
    print("Для выхода из приложения используйте /exit")


def print_history(mode):#печать истории диалога
    dialog = json.loads(client.recv(4096).decode())  # получаем историю
    print('Вы' + ' ' * (len_field - 2 - len(name_original)) + name_original)
    print("_" * len_field)
    count_mes = 0
    max_count_mes = 10#изначально выводится 10 сообщений, чтобы поулчить все сообщения /all
    if mode == 1:
        max_count_mes = 0
    for i in dialog.get('messages'):  # выводим её
        if count_mes < len(dialog.get('messages')) - max_count_mes and mode == 0:
            count_mes += 1
            continue
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
    client = ssl.wrap_socket(client, keyfile="path/to/keyfile", certfile="path/to/certfile")    #Нужно генерировать сертификат и ключ, например с помощью OpenSSL
    client.connect((SERVER, PORT))
    public_key_from_server = pickle.loads(client.recv(4096))
    public_key, privat_key = rsa.newkeys(512)
    key = pickle.dumps(public_key)
    client.send(key)
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
                send_encode_msg(send_login, public_key_from_server)
                ans = rsa.decrypt(client.recv(4096), privat_key).decode() #ждём результат запроса
                if ans == '1':
                    clear_console()
                    print("Вы успешно вошли")
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
                print(wrong_parameters)
        except:
            clear_console()
            print(wrong_parameters)

    print("Введите имя пользователя которому хотите написать:") #после логина ищем чубрика которому хотим написать
    while True: #Основное 'меню' чата
        name = input()
        name_original = name
        name = 'F' + name + " " + login
        send_encode_msg(name, public_key_from_server)

        ans = rsa.decrypt(client.recv(4096), privat_key).decode() #ждём овтета
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
            mode = rsa.decrypt(client.recv(4096), privat_key).decode()
            if mode == '1': #если есть история диалога
                print_history(0) #выводим историю
            print("Чтобы узнать команды отправьте /help")
            print(input_message)
            while True: #начинаем диалог
                message = input()
                if message == '/all':
                    clear_console()
                    msg = "R" + login + " " + name_original
                    send_encode_msg(msg, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()
                    print_history(1)
                    print(input_message)
                    continue
                elif message == '/upload':
                    Tk().withdraw() #окно выбора файла(у меня работает почему то только в дебаге)
                    path_to_file = askopenfilename()
                    check = path_to_file.find('/')
                    if check == -1: #если папка корневая
                        name_of_file = path_to_file
                    else:
                        name_of_file = path_to_file[path_to_file.rfind('/')+1:]#парс имени сообщения из пути
                    msg = "U" + login + " "+ name_original
                    send_encode_msg(msg, public_key_from_server)
                    time.sleep(0.5)
                    send_encode_msg(name_of_file, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()  # 1 - всё ок, 0 - файл не уинкальный
                    if mode == '0':
                        print("Название файла должно быть уникальным")
                        continue
                    time.sleep(0.5)
                    file_stats = os.stat(path_to_file).st_size / 1024 #отпарвляем размер файла(КБ)
                    if file_stats != int(file_stats):
                        file_stats = int(file_stats) + 1
                    send_encode_msg(f'{file_stats}', public_key_from_server)
                    time.sleep(0.5)

                    f = open(path_to_file, "rb")

                    l = f.read(1024)
                    while (l):
                        # отправляем строку на сервер
                        client.send(l)
                        l = f.read(1024)
                    time.sleep(0.5)
                    f.close()
                    clear_console()
                    msg = "R" + login + " " + name_original
                    send_encode_msg(msg, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()
                    print_history(0)  # выводим обновлённый диалог
                    print("Файл удачно отправлен")
                    print(input_message)
                    continue
                elif message[:9] == '/download':  #
                    msg = "D" + login + " " + name_original
                    send_encode_msg(msg, public_key_from_server)
                    name_of_file = message[message.find(' ') + 1:]
                    time.sleep(0.5)
                    send_encode_msg(name_of_file, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()
                    if mode == "0":
                        print("Такого файла нет")
                        continue
                    size = rsa.decrypt(client.recv(4096), privat_key).decode()
                    f = open(name_of_file, 'wb')
                    count = 0
                    while True:
                        l = client.recv(1024)
                        f.write(l)
                        count += 1
                        if not l:
                            break
                        if count == int(size):
                            break
                    f.close()
                    clear_console()
                    msg = "R" + login + " " + name_original
                    send_encode_msg(msg, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()
                    print_history(0)  # выводим обновлённый диалог
                    print("Файл успешно загружен")
                    print(input_message)
                    continue
                elif message == '/update':
                    msg = "R" + login + " " + name_original
                    send_encode_msg(msg, public_key_from_server)
                    mode = rsa.decrypt(client.recv(4096), privat_key).decode()
                    clear_console()
                    print_history(0)  # выводим обновлённый диалог
                    print(input_message)
                    continue
                elif message == '/back':
                    clear_console()
                    print("Введите имя пользователя которому хотите написать:")
                    break
                elif message == '/exit':
                    print("Надеюсь ещё увидимся. До свидания)")
                    exit()
                elif message == '/help':
                    commands()
                    continue
                elif message[0] == '/':
                    print("Некорректная команда, для получения списка всех команд используйте /help")
                info = "M" + login + " " + name_original
                send_encode_msg(info, public_key_from_server) #отпаряем данные кто и кому
                time.sleep(0.5)
                send_encode_msg(message, public_key_from_server) #отпарляем сообщение
                time.sleep(0.5)
                msg = "R"+login+" "+name_original
                send_encode_msg(msg, public_key_from_server)#отпарялем запрос на обноваление диалога
                mode = rsa.decrypt(client.recv(4096), privat_key).decode() #ответ 1 - есть диалог 0 - диалог пустой
                if mode == "1":
                    clear_console()
                    print_history(0)#выводим обновлённый диалог
                    print(input_message)