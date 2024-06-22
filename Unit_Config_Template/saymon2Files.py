#/usr/bin/python3


import requests
import base64
import json
import os

# Создания иерархии объектов в файловой системе из SAYMON


# SAYMON Server
#SAYMON_ORIGIN = {"host": "http://127.0.0.1:8080",  # С указанием протокола
#                 "user": "admin",
#                 "password": "saymon",
#                 "object": "65e5bc7418a5fa1ac45a6514"}


headers = {'content-type': 'application/json'}

headers_base64 = {
    'content-type': "multipart/form-data; boundary=----WebKitFormBoundaryX8fA8XEeEPGLzgaq",
    'cache-control': "no-cache"
}



OneJSONFile = True # Создавать общий JSON

Working_Directory = ''

JsonDataOne = []

#/usr/bin/python3


import requests
import base64
import json
import os

# Создания иерархии объектов в файловой системе из SAYMON


# SAYMON Server
SAYMON_ORIGIN = {"host": "http://127.0.0.1:8080",  # С указанием протокола
                 "user": "admin",
                 "password": "saymon",
                 "object": "65e5a49e49147e1c1d27d469"}


headers = {'content-type': 'application/json'}

headers_base64 = {
    'content-type': "multipart/form-data; boundary=----WebKitFormBoundaryX8fA8XEeEPGLzgaq",
    'cache-control': "no-cache"
}



OneJSONFile = True # Создавать общий JSON

Working_Directory = ''

JsonDataOne = []


def getObject(host=SAYMON_ORIGIN['host'], object=SAYMON_ORIGIN['object'], user=SAYMON_ORIGIN['user'],
              password=SAYMON_ORIGIN['password']):
    """Получает объект по id"""
    try:
        response = requests.get(url=host + '/node/api/objects/' + object + '',
                                auth=(user, password), headers=headers)
        return json.loads(response.text)
    except:
        return False


def getAllObject(host=SAYMON_ORIGIN['host'], object=SAYMON_ORIGIN['object'], user=SAYMON_ORIGIN['user'],
                 password=SAYMON_ORIGIN['password']):
    """Получает все объекты"""
    try:
        response = requests.get(url=host + '/node/api/objects/' + object + '',
                                auth=(user, password), headers=headers)
        return json.loads(response.text)

    except:
        return False

def downloadImg(uid, host=SAYMON_ORIGIN['host'], user=SAYMON_ORIGIN['user'], password=SAYMON_ORIGIN['password']):
    """Скачивает изображение по uid"""
    try:
        file = requests.get(url=host + 'node-resources/images/uid/' + uid,
                            stream=True, headers=headers, auth=(user, password)).content
        ## Может возникнуть проблема с jpeg, декодирование utf может вызвать ошибку. Нужно переделать проверку
        #if file.decode("utf8").find("code") > 0:
        #    return False
        #else:
        return base64.b64encode(file)
    except Exception as err:
        print("downloadImg", err)
        return False

def checkBackground(object):
    """Проверяет наличие фонового изображения и скачивает его"""
    try:
        object_groups = []
        imgName = object["background"]
        img = downloadImg(imgName)
        if img == False:
            print("checkBackground, error download img")
        with open(imgName, "wb") as fh:
            fh.write(base64.decodebytes(img))
        return img
    except Exception as err:
        # print(err)
        return False

def createOneJsonFile(data):
    """Создает один JSON-файл со всеми данными объектов"""
    with open(SAYMON_ORIGIN['host'].replace("https://", '').replace("http://", '').replace('/', '')+'.json', 'w+') as outfile:
        json.dump(data, outfile, sort_keys=False, indent=4, ensure_ascii=False)

def createJsonFile(data):
    """Создает JSON-файл для каждого объекта"""
    with open(data['id'] + '.json', 'w+') as outfile:
        json.dump(data, outfile, sort_keys=False, indent=4, ensure_ascii=False)

def createStyleFile(data):
    """Создает CSS-файл со стилями объекта"""
    with open(data['id'] + '.css', 'w+') as outfile:
        data = str(json.loads(data['client_data'])['custom_style'])
        data = data.replace('{', '{\n').replace('}', '\n}')
        outfile.write(data)

def recCreate(id, one = 0):
    """Рекурсивно создает иерархию объектов"""
    global JsonDataOne
    try:
        object = getObject(object=id)
        if one:
            JsonDataOne.append(object)
        os.mkdir(object['id'])
        os.chdir(object['id'])
        checkBackground(object)
        createJsonFile(object)
#        createStyleFile(object)

        for child in object['child_ids']:
                recCreate(child, OneJSONFile)
        os.chdir('..')
        # else:
        #     print("Ошибка rec getObject")
    except Exception as err:
        print("Ошибка в рекусрии", err)
        exit()

def main():
    """Основная функция"""
#    dir_name = SAYMON_ORIGIN['host'].replace("https://", '').replace("http://", '').replace('/', '')
    dir_name = 'saymon2Files'
    try:
        os.mkdir(dir_name)
        os.chdir(dir_name)

        if OneJSONFile:
            recCreate(SAYMON_ORIGIN['object'], OneJSONFile)
            createOneJsonFile(JsonDataOne)
        else:
            recCreate(SAYMON_ORIGIN['object'])
    except Exception as err:
        print(err)
        exit()

if __name__ == "__main__":
    main()
    print('Готово!')

    # Данный код на Python предназначен для создания иерархии объектов файловой системы на основе данных из системы SAYMON.

    # Функции:

    # getObject(): Получает объект по его идентификатору из SAYMON.
    # getAllObject(): Получает все объекты из SAYMON.
    # downloadImg(): Загружает изображение по его идентификатору из SAYMON.
    # checkBackground(): Проверяет наличие фонового изображения у объекта и загружает его, если оно есть.
    # createOneJsonFile(): Создает один JSON-файл со всеми данными объектов.
    # createJsonFile(): Создает отдельный JSON-файл для каждого объекта.
    # createStyleFile(): Создает CSS-файл со стилями для каждого объекта.
    # recCreate(): Рекурсивно создает иерархию объектов файловой системы и соответствующие файлы.
    # main(): Точка входа в программу.

    # Логика программы:

    # Программа создает каталог с именем, полученным из URL-адреса сервера SAYMON.
    # Программа переходит в созданный каталог.
    # Программа рекурсивно создает иерархию объектов файловой системы, загружая данные из SAYMON и создавая соответствующие файлы.
    # Если указан флаг OneJSONFile, программа создает один JSON-файл со всеми данными объектов.
    # В противном случае программа создает отдельные JSON-файлы для каждого объекта.
    # Программа создает CSS-файлы со стилями для каждого объекта.
    # Программа выводит сообщение "Готово!" после завершения работы.

    # Использование:

    # Для использования программы необходимо указать параметры сервера SAYMON (адрес хоста, пользователя, пароль, идентификатор объекта) в словаре SAYMON_ORIGIN. Затем запустить программу с помощью команды python3 script.py
