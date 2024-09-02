import sys
import warnings
warnings.filterwarnings("ignore")

import json
import requests
import time,os
from datetime import datetime, timezone

import pandas as pd
import datetime as DT
#import numpy as np
from pandasql import sqldf
pysqldf = lambda q: sqldf(q, globals())
import re

################### Выбрать требуемый конфиг и рабочая папка #######
import laim_session_config_gpn as ls
####################################################################

# import sheepSaymon
import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)
import laim_import_saymon_api as li
import laim_export_saymon_api as le


def def_refresh_objects():
    # Объявляем использование глобальных переменных в функции
    global objects_in_tree  # Счетчик объектов в дереве
    global objects_created  # Счетчик созданных объектов
    global objects_updated  # Счетчик обновленных объектов
    global errors_commited  # Счетчик ошибок, произошедших во время выполнения
    global df_obj_tree      # DataFrame, который будет хранить дерево объектов

    # Логирование начала процесса загрузки дерева объектов
    ll.print_log.info(" - Loading object tree")

    # Загрузка дерева объектов из API и преобразование его в DataFrame
    df_obj_tree = pd.json_normalize(li.get_objects_tree())

    # Проверка наличия ошибки "InvalidCredentials" в полученных данных
    if ('InvalidCredentials' in df_obj_tree.values):
        # Логирование предупреждения о неверных учетных данных
        ll.print_log.warn(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " - Invalid credentials")
        # Увеличение счетчика ошибок
        errors_commited = errors_commited + 1
        # Выход из функции и, возможно, программы
        sys.exit()

    # Проверка наличия ошибки "NotFound" в данных
    if ('NotFound' in df_obj_tree.values):
        # Логирование предупреждения о том, что объекты не найдены
        ll.print_log.warn(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " - No objects in Saymon")
        # Увеличение счетчика ошибок
        errors_commited = errors_commited + 1
        # Выход из функции и, возможно, программы
        sys.exit()

    # Удаление столбца 'parent_id' из DataFrame
    del df_obj_tree['parent_id']

    # Логирование успешной загрузки дерева объектов
    ll.print_log.info(" - Loaded object('s tree)")

    # Сохранение обработанного DataFrame в CSV-файл
    df_obj_tree.to_csv('./reports/obj_metr_flat.csv')

    # Преобразование столбца 'child_ids' в строковый тип данных
    df_obj_tree['child_ids'] = df_obj_tree['child_ids'].astype("string")

def def_create_group_services():
    # Объявление глобальных переменных для использования внутри функции.
    global objects_in_tree  # Текущее количество объектов в дереве.
    global objects_created  # Общее количество созданных объектов в этой сессии.
    global objects_updated  # Общее количество обновленных объектов в этой сессии.
    global errors_commited  # Счетчик ошибок, возникших в ходе выполнения.

    # Определение SQL запроса для выборки уникальных записей, которые требуют создания новых групп сервисов
    query = """
    SELECT DISTINCT 
    rsm.rsm_obj_to_create_under,  -- Столбец rsm_obj_to_create_under из таблицы rsm
    rsm.service_group,            -- Столбец service_group из таблицы rsm
    full.name,                    -- Столбец name из таблицы full
    full.id                       -- Столбец id из таблицы full
    FROM df_rsm_bulk AS rsm            -- Основная таблица df_rsm_bulk с псевдонимом rsm
    LEFT JOIN df_obj_tree AS full           -- Левое соединение с таблицей df_obj_tree с псевдонимом full
    ON full.name = rsm.service_group -- Условие соединения: name из full должно совпадать с service_group из rsm
    WHERE full.id IS NULL               -- Условие фильтрации: выбираем только те строки, где id из full равно NULL
    """

    # Выполнение SQL запроса, результат сохраняется в DataFrame.
    try:
        df_result_sql = pysqldf(query)
    except Exception as e:
        print("Произошла ошибка при выполнении запроса:", e)

    # Сохранение результатов запроса в файл CSV для аудита и дальнейшего анализа.
    df_result_sql.to_csv('./reports/df_result_sql.csv')

    # Проход по всем строкам результата SQL запроса для обработки каждой строки отдельно.
    for row in df_result_sql.iterrows():
        # Проверка, задан ли родительский объект для создания сервисной группы. Если нет, то ошибка.
        if row[1]['rsm_obj_to_create_under'] == None:
            # В зависимости от режима выполнения, выводится сообщение об ошибке.
            if ls.just_check:
                print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
                      :-3] + ' --- Проверьте на предмет пустых строк или формата файла скрипта bulk_input. Остановка скрипта.')
            else:
                ll.print_log.info('Проверьте на предмет пустых строк или формата файла скрипта bulk_input. Остановка скрипта.')
                errors_commited = errors_commited + 1  # Инкремент счетчика ошибок.
                sys.exit()  # Прекращение выполнения функции.

        # Определяем источник данных - таблицу df_obj_tree, где хранятся уже существующие объекты
        # Условие выборки: ищем объект, чье имя совпадает с именем, указанным как потенциальный родитель для создания группы сервисов
        query = f"""
            -- Выбираем уникальные значения столбца id из таблицы df_obj_tree
            SELECT DISTINCT full.id 
            -- Из таблицы df_obj_tree с псевдонимом full
            FROM df_obj_tree as full
            -- Условие фильтрации: выбираем строки, где значение столбца name 
            -- совпадает со значением столбца rsm_obj_to_create_under из строки row[1]
            WHERE full.name = '{row[1]['rsm_obj_to_create_under']}'
            """

        df_result_sql_parent = sqldf(query)
        df_result_sql_parent.to_csv('./reports/df_result_sql_parent.csv')

        # Проверка наличия родительского объекта.
        if df_result_sql_parent.empty:
            ll.print_log.info('В SAYMON или файле'\
                ' скрипта bulk_input отсутствует объект первичной привязки - поле rsm_obj_to_create_under.')
            errors_commited = errors_commited + 1
            sys.exit()

        # Подготовка свойств для создания новой группы сервисов.
        prop = [{"name":"РСМ.Служба","value":str(row[1]['service_group']),"type_id":1}]

        # Проверка режима выполнения: только проверка или выполнение создания объекта.
        if ls.just_check:
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
                      :-3] + ' --- Try create object service group:' + str(row[1]['service_group'])+ ' under '+ str(df_result_sql_parent['id'].values[0]))
            objects_created = objects_created + 1
        else:
            # Попытка создать объект сервисной группы с использованием API.
            try:
                ll.print_log.info(' --- Try create object service group:' + str(row[1]['service_group']) + ' under '+ str(df_result_sql_parent['id'].values[0]))
                created_obj = le.def_create_an_object(
                    cr_name=row[1]['service_group'], cr_parent=df_result_sql_parent['id'].values[0], cr_class= 30)
                if created_obj != []:
                    objects_created = objects_created + 1
            except Exception as err:
                ll.print_log.info('Проверьте на предмет пустых строк или формата файла скрипта bulk_input. Остановка скрипта на ошибке:' + str(err))
                errors_commited = errors_commited + 1
                sys.exit()

def def_create_services():

    # Объявление глобальных переменных для использования внутри функции
    global objects_in_tree  # Счетчик объектов в дереве
    global objects_created  # Счетчик созданных объектов
    global objects_updated  # Счетчик обновленных объектов
    global errors_commited  # Счетчик ошибок

    # Формирование SQL запроса для идентификации сервисов, которые еще не созданы в системе управления.
    query = f"SELECT DISTINCT full.id, " \
            f"       full.name, " \
            f"       rsm.service_group, " \
            f"       rsm.service_name " \
    f"FROM df_rsm_bulk as rsm " \
    f"LEFT JOIN df_obj_tree as full " \
    f"ON full.name = rsm.service_name " \
    f"WHERE full.id is null " \
    f"AND rsm.service_name is not null "


    # Выполнение SQL запроса и сохранение результатов в DataFrame.
    df_result_sql = sqldf(query)
    # Сохранение данных о ненайденных сервисах в CSV файл.
    df_result_sql.to_csv('./reports/services_lost.csv')

    # Обработка каждой строки в полученном DataFrame.
    for row in df_result_sql.iterrows():
        # Поиск ID для родительской группы сервисов, в которую будет включен новый сервис.
        query = f"SELECT DISTINCT full.id " \
                f"FROM df_obj_tree as full " \
        f"WHERE full.name = '{row[1]['service_group']}'"
        # Выполнение SQL запроса для получения ID родительской группы сервисов.
        df_result_sql_parent = sqldf(query)

        prop = []  # Инициализация списка свойств для создаваемого сервиса.

        # Проверка, выполняется ли скрипт в режиме тестирования.
        if ls.just_check:
            # В режиме тестирования выводится сообщение с предложением создать сервис,
            # без реального выполнения операции создания.
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] +
                  ' --- Try create object service: ', row[1]['service_name'])
            objects_created += 1  # Инкремент количества "созданных" объектов.
        else:
            # В рабочем режиме логируется попытка создания сервиса.
            ll.print_log.info(' --- Create object service: ' + str(row[1]['service_name']))
            # Создание объекта сервиса через API.
            created_obj = le.def_create_an_object(
                cr_name=row[1]['service_name'],
                cr_parent=df_result_sql_parent['id'].values[0],
                cr_class=15,
                cr_prop=prop)
            # Проверка успешности создания объекта и инкремент счетчика созданных объектов.
            if created_obj != []:
                objects_created += 1

def def_custom_oms_VM_pin():
    # Использование глобальных переменных для отслеживания статуса операций
    global objects_in_tree
    global objects_created
    global objects_updated
    global errors_commited

    # Инициализация списка для хранения объектов ВМ, полученных из API
    oms_vm1 = []

    # Подготовка запроса для API: поиск всех объектов ВМ с определенным префиксом в имени
    data = {
        "search": {
            "name": {
                "$regex": "^_OMS02.*$", # Регулярное выражение для Омских ВМ
                "$options": "i"  # Регистронезависимый поиск
            },
            "class_id": ls.graph_VM_class_id  # Фильтр по классу графических виртуальных машин
        }
    }

    # Вызов функции поиска с использованием подготовленных параметров
    dash = li.def_search_anything(data)
    # Добавление результатов в список oms_vm1
    oms_vm1.append(dash)

    # Проверка режима исполнения: вывод информации или выполнение изменений
    if ls.just_check:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- ГВМ Омска на виде:', len(oms_vm1[0]))
        return
    else:
        ll.print_log.info(' --- ГВМ Омска на виде:' + str(len(oms_vm1[0])))

    # Сортировка объектов по имени для последовательной обработки
    new1 = sorted(oms_vm1[0], key=lambda d: d['name'])

    # Начальные параметры для расстановки объектов на виде
    shift_left = ls.oms_shift_left
    shift_left += ls.step_left
    shift_left_init = shift_left

    shift_top = ls.oms_shift_top
    shift_top -= ls.step_top
    shift_top_init = shift_top

    # Инициализация переменных для определения положения объекта в ряду
    name_line = 1
    name_row = 0
    num_in_line = 18

    # Обработка каждого объекта для расстановки
    for i in range(len(new1)):
        z_index = 100 + i
        shift_left -= ls.step_left
        shift_top += ls.step_top
        if (i / num_in_line).is_integer():
            name_row = 0
            name_line += 1
            shift_left = shift_left_init + (i / num_in_line - 1) * ls.step_left
            shift_top = shift_top_init + (i / num_in_line + 1) * ls.step_top
        name_row += 1
        if ls.just_check:
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Выравниваем ГВМ Омска на виде:', new1[i]['id'], ' ', new1[i]['name'], 'top - ', int(shift_top), 'left - ', int(shift_left))
        else:
            try:
                # Подготовка данных для обновления стиля отображения объекта
                client_data = "{\"headlinePropIds\":[],\"custom_style\":{\"zIndex\":" + str(z_index) + ",\"left\":\"" + str(int(shift_left)) + "px\",\"top\":\"" + str(int(shift_top)) + "px\",\"width\":\"28px\",\"height\":\"50px\"},\"nonPinnedSections\":{\"widgets\":\"true\",\"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\"entity-state-conditions\":\"true\",\"entity-incident-conditions\":\"true\",\"state-triggers\":\"true\",\"stat-rules\":\"true\",\"properties\":false,\"documents\":\"true\",\"operations\":\"true\",\"operations-history\":\"true\",\"state-history\":\"true\",\"audit-log\":\"true\",\"history-graph\":\"true\"},\"collapseSections\":{\"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\"properties\":false,\"documents\":\"true\"}}"
                # Обновление объекта с новым стилем
                updated_obj = le.def_update_an_object(cr_obj_id=new1[i]['id'], cr_client_data=client_data)
                # Проверка результата обновления
                if updated_obj == None:
                    pass
                elif updated_obj['id'] != '':
                    objects_updated += 1
                    ll.print_log.info(' --- Выравниваем ГВМ Омска на виде:' + str(new1[i]['id']) + ' ' + str(new1[i]['name']) + '; top - ' + str(int(shift_top)) + '; left - ' + str(int(shift_left)))
                elif updated_obj['errors'] != 0:
                    ll.print_log.info(' --- Не удалось выравнять объект' + str(new1[i]['id']) + ' ' + str(new1[i]['name']))
                    errors_commited += int(updated_obj['errors'])
            except Exception as err:
                ll.print_log.info(' --- Выравнивание ГВМ Омска на виде не выполнено:' + str(err))
                errors_commited += 1

def def_custom_msk_VM_pin():
    # Использование глобальных переменных для отслеживания состояния объектов в системе
    global objects_in_tree
    global objects_created
    global objects_updated
    global errors_commited

    # Инициализация списка для хранения результатов запроса по ВМ
    msk_vm2 = []
    # Конфигурация запроса для API, нацеленного на поиск графических ВМ в Москве
    data = {"search":{
      "name": {
        "$regex": "^_MSK05.*$", # Регулярное выражение для идентификации Московских ВМ
        "$options": "i"  # Регистронезависимый поиск
      },
      "class_id": ls.graph_VM_class_id # Идентификатор класса для графических ВМ
    }
    }

    # Вызов функции API для поиска данных по заданным критериям
    dash = li.def_search_anything(data)
    # Добавление полученных данных в список
    msk_vm2.append(dash)

    # Проверка на режим только проверки без выполнения изменений
    if ls.just_check:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
                :-3] + ' --- ГВМ Москвы на виде:',len(msk_vm2[0]))
        return
    else:
        # Запись в лог количество найденных ВМ
        ll.print_log.info(' --- ГВМ Москвы на виде:'+ str(len(msk_vm2[0])))

    # Сортировка найденных ВМ по имени для последовательной обработки
    new2 = sorted(msk_vm2[0], key=lambda d: d['name'])

    # Инициализация параметров для расстановки ВМ на виде
    shift_left = ls.msk_shift_left
    shift_left += ls.step_left
    shift_left_init = shift_left

    shift_top = ls.msk_shift_top
    shift_top -= ls.step_top
    shift_top_init = shift_top

    name_line = 1
    name_row = 0
    num_in_line = 18

    # Перебор всех ВМ для установки координат и применения стилей
    for i in range(len(new2)):
        z_index = 100+i
        shift_left -= ls.step_left
        shift_top += ls.step_top
        # Проверка на начало новой строки объектов
        if (i / num_in_line).is_integer():
            name_row = 0
            name_line += 1
            shift_left = shift_left_init + (i / num_in_line - 1) * ls.step_left
            shift_top = shift_top_init + (i / num_in_line + 1) * ls.step_top
        name_row += 1

        if ls.just_check:
            # В режиме проверки вывод координат для каждого объекта
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
                    :-3] + ' --- Выравниваем ГВМ Москвы на виде:', new2[i]['id'], ' ', new2[i]['name'],
                    'top - ', int(shift_top), 'left - ', int(shift_left))
        else:
            try:
                # Подготовка данных для обновления объекта
                client_data = "{\"headlinePropIds\":[],\"custom_style\":{\"zIndex\":" + str(z_index) + \
                              ",\"left\":\"" + str(int(shift_left)) + "px\",\"top\":\"" + str(int(shift_top)) + \
                              "px\",\"width\":\"28px\",\"height\":\"50px\"},\"nonPinnedSections\":{\"widgets\":\"true\",\
                              \"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                              \"entity-state-conditions\":\"true\",\"entity-incident-conditions\":\"true\",\
                              \"state-triggers\":\"true\",\"stat-rules\":\"true\",\"properties\":false,\
                              \"documents\":\"true\",\"operations\":\"true\",\"operations-history\":\"true\",\
                              \"state-history\":\"true\",\"audit-log\":\"true\",\"history-graph\":\"true\"},\
                              \"collapseSections\":{\"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                              \"properties\":false,\"documents\":\"true\"}}"
                # Выполнение обновления объекта с новыми данными
                updated_obj = le.def_update_an_object(cr_obj_id=new2[i]['id'], cr_client_data=client_data)
                if updated_obj is None:
                    pass
                elif updated_obj['id'] != '':
                    objects_updated += 1
                    ll.print_log.info(' --- Выравниваем ГВМ Москвы на виде:' + str(new2[i]['id']) + ' ' + str(new2[i]['name']) +
                                     '; top - ' + str(int(shift_top)) + '; left - ' + str(int(shift_left)))
                elif updated_obj['errors'] != 0:
                    ll.print_log.info(' --- Не удалось выравнять объект' + str(new2[i]['id']) + ' ' + str(new2[i]['name']))
                    errors_commited += int(updated_obj['errors'])
            except Exception as err:
                ll.print_log.info(' --- Выравнивание ГВМ Москвы на виде не выполнено:' + str(err))
                errors_commited += 1

def def_custom_vm_pin(location):
    # Использование глобальных переменных для отслеживания состояния операций
    global objects_in_tree
    global objects_created
    global objects_updated
    global errors_commited

    # Создание пустого списка для хранения данных о ВМ
    vm2 = []

    # Определение параметров для API-запроса на получение ВМ по регулярному выражению, основанному на локации
    data = {
        "search": {
            "name": {
                "$regex": "^_" + location + ".*$",  # Поиск ВМ, начинающихся с заданной локации
                "$options": "i"  # Регистронезависимый поиск
            },
            "class_id": ls.graph_vm_class_id  # Фильтрация по классу графических ВМ
        }
    }

    # Выполнение поиска по заданным критериям через API
    dash = li.def_search_anything(data)
    # Добавление результатов в список
    vm2.append(dash)

    # Проверка, выполняется ли код в режиме только для проверки (не внося изменений)
    if ls.just_check:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
            :-3] + ' --- ГВМ ' + location + ' на виде:', len(vm2[0]))
        return
    else:
        # Логирование количества найденных ВМ в зависимости от локации
        ll.print_log.info(' --- ГВМ ' + location + ' на виде:' + str(len(vm2[0])))

    # Сортировка ВМ по имени для последовательной обработки
    new2 = sorted(vm2[0], key=lambda d: d['name'])

    # Установка начальных параметров для расстановки ВМ на "виде" или схеме
    shift_left = int(ls.position_dict[location]["shift_left"])
    shift_left += int(ls.position_dict[location]["step_left"])
    shift_left_init = shift_left

    shift_top = int(ls.position_dict[location]["shift_top"])
    shift_top -= int(ls.position_dict[location]["step_top"])
    shift_top_init = shift_top

    # Инициализация счетчиков для расстановки объектов
    name_line = 1
    name_row = 0
    num_in_line = 18

    # Проход по каждому объекту для настройки его позиции
    for i in range(len(new2)):
        z_index = 100 + i
        shift_left -= int(ls.position_dict[location]["step_left"])
        shift_top += int(ls.position_dict[location]["step_top"])
        # Проверка на начало новой линии объектов
        if (i / num_in_line).is_integer():
            name_row = 0
            name_line += 1
            shift_left = shift_left_init + (i / num_in_line - 1) * int(ls.position_dict[location]["step_left"])
            shift_top = shift_top_init + (i / num_in_line + 1) * int(ls.position_dict[location]["step_top"])
        name_row += 1

        # В режиме только проверки выводятся предполагаемые координаты
        if ls.just_check:
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
                  :-3] + ' --- Выравниваем ГВМ ' + location + ' на виде:', new2[i]['id'], ' ', new2[i]['name'],
                  'top - ', int(shift_top), 'left - ', int(shift_left))
        else:
            try:
                # Формирование данных для обновления стиля объекта
                client_data = "{\"headlinePropIds\":[],\"custom_style\":{\"zIndex\":" + str(z_index) + \
                              ",\"left\":\"" + str(int(shift_left)) + "px\",\"top\":\"" + str(int(shift_top)) + \
                              "px\",\"width\":\"28px\",\"height\":\"50px\"},\"nonPinnedSections\":{\"widgets\":\"true\",\
                              \"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                              \"entity-state-conditions\":\"true\",\"entity-incident-conditions\":\"true\",\
                              \"state-triggers\":\"true\",\"stat-rules\":\"true\",\"properties\":false,\
                              \"documents\":\"true\",\"operations\":\"true\",\"operations-history\":\"true\",\
                              \"state-history\":\"true\",\"audit-log\":\"true\",\"history-graph\":\"true\"},\
                              \"collapseSections\":{\"stat\":\"true\",\"entity-settings\":\"true\",\"monitoring\":\"true\",\
                              \"properties\":false,\"documents\":\"true\"}}"
                updated_obj = le.def_update_an_object(cr_obj_id=new2[i]['id'], cr_client_data=client_data)
                # Обновление объекта с новым стилем через API
                updated_obj = le.def_update_an_object(cr_obj_id=new2[i]['id'], cr_client_data=client_data)
                if updated_obj is None:
                    pass
                elif updated_obj['id'] != '':
                    objects_updated += 1
                    ll.print_log.info(' --- Выравниваем ГВМ ' + location + ' на виде:' + str(new2[i]['id']) + ' ' + str(new2[i]['name']) +
                                      '; top - ' + str(int(shift_top)) + '; left - ' + str(int(shift_left)))
                elif updated_obj['errors'] != 0:
                    ll.print_log.info(' --- Не удалось выравнять объект' + str(new2[i]['id']) + ' ' + str(new2[i]['name']))
                    errors_commited += int(updated_obj['errors'])
            except Exception as err:
                ll.print_log.info(' --- Выравнивание ГВМ ' + location + ' на виде не выполнено:' + str(err))
                errors_commited += 1

def def_auto_ping_discovered_hosts():
    global objects_in_tree
    global objects_created
    global objects_updated
    global errors_commited
    #7. Если была процедура AutoPingDiscovery.
    # Совмещаем таблички - целевую и существующую, перебор, переименование и привязка хостов по IP адресу
    print('7. Совмещаем таблички - целевую и существующую, перебор, переименование и привязка хостов по IP адресу')
    # query = f"SELECT full.id, "\
    #         f"       full.name, "\
    #         f"       rsm.service_group, "\
    #         f"       rsm.service_name, "\
    #         f"       rsm.trg_name, "\
    #         f"       rsm.type_property, "\
    #         f"       rsm.role_property, "\
    #         f"       rsm.host_ip, "\
    #         f"       rsm.mask_property, "\
    #         f"       rsm.gate_property, "\
    #         f"       rsm.vlan_property, "\
    #         f"       rsm.os_tag, "\
    #         f"       rsm.landscape_tag "\
    #         f"FROM df_obj_tree as full "\
    #         f"JOIN df_rsm_bulk as rsm "\
    #         f"ON full.name = rsm.host_ip "
    # #        f"WHERE full.id is null " #Можно найти отсутствующие хосты добавить LEFT!
    # df_result_sql= sqldf(query)
    # df_result_sql.to_csv('./reports/host_descr.csv')
    # for row in df_result_sql.iterrows():
    #         #Найти id сервиса для хоста
    #         query = f"SELECT DISTINCT full.id "\
    #                 f"FROM df_obj_tree as full "\
    #                 f"WHERE full.name = '{row[1]['service_name']}' "
    #         df_result_sql_parent= sqldf(query)
    #         prop=[]
    ## Добавить формирование набора свойств из файла

    #         updated_host= le.def_update_an_object(cr_obj_id= row[1]['id'],
    #                       cr_name= row[1]['trg_name'],
    #                       cr_parent= df_result_sql_parent['id'].values[0],
    #                       cr_prop=prop,
    #                       cr_tag_id= '') #to update tags from properties if needed

    # #8. Обновляем существующие сервисы и группы сервисов (имена объектов) с учетом вновь созданных
    # print('8. Обновляем существующие сервисы и группы сервисов (имена объектов) с учетом вновь созданных')
    # print(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+" - Loading object tree")
    # def_refresh_objects()

    # #10. Прописываем свойства и запускаем мониторинги на созданных объектах
    #         print('10. Прописываем свойства и запускаем мониторинги на созданных объектах №'+ str(row['№'])+ '& Name:' + str(row['trg_name']))
    #         prop=[]
    #         prop.append( {"name":"Net mask",  "value":str(row['mask_property']), "type_id":1} )#optional
    #         prop.append( {"name":"Gate",    "value":str(row['gate_property']), "type_id":1} )#optional
    #         prop.append( {"name":"VLAN",      "value":str(row['vlan_property']), "type_id":1} )#optional
    #         prop.append( {"name":"OS",        "value":str(row['os_tag']),        "type_id":1} )#optional
    #         prop.append( {"name":"Landscape", "value":str(row['landscape_tag']), "type_id":1} )#optional
    #         prop.append( {"name":"IP",     "value":str(row['host_ip']),       "type_id":1} )#optional
    # #my_property
    #         if (row['my_property'] != '') and row['my_property'] != None: #можем добавить свое свойство my_property например для фильтра
    #             my_property = row['my_property'].split(":")
    #             prop.append( {"name":my_property[0],"value":my_property[1],       "type_id":1} )#optional
    #prop: list
    #        for props in row[1].filter(regex=r"WORDABC9(?=[^\d]|$)")['prop:']
    #address
            # prop.append( {"name":"Address","value":str(row['host_ip']),"type_id":1} )# update existing property_id
            # if row['mon_httpRequest_on'] == 'Y':
            # #create child object Ping
            #     prop.append( {"name":"TaskType",  "value":"httpRequest","type_id":8} )#monitoring set
            # #ping
            #     prop.append( {"name":"AgentId",   "value":str(row['mon_agent_id']), "type_id":8} )#monitoring set
            #     prop.append( {"name":"PingPacketsCount","value":str(row['mon_PingPacketsCount']),"type_id":8} )#monitoring set ;
            #     prop.append( {"name":"PingTimeout","value":str(row['mon_PingTimeout']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"PingHost","value":str(row['host_ip']),"type_id":8} )#monitoring set
            # elif row['mon_ping_on'] == 'Y':
            # #create child object HTTP GET
            #     prop.append( {"name":"TaskType",  "value":"ping","type_id":8} )#monitoring set
            # #http get
            #     prop.append( {"name":"HttpRequestMethod","value":str(row['mon_HttpRequestMethod']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"HttpRequestUrl","value":str(row['mon_HttpRequestUrl']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"HttpRequestIncludeResponseBody","value":str(row['mon_HttpRequestIncludeResponseBody']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"HttpRequestForceParse","value":str(row['mon_HttpRequestForceParse']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"TaskPeriodUnit","value":str(row['mon_TaskPeriodUnit']),"type_id":8} )#monitoring set
            #     prop.append( {"name":"TaskPeriodValue","value":str(row['mon_TaskPeriodValue']),"type_id":8} )#monitoring set
            # prop = list(filter((lambda item: item['value'] != 'None'), prop))
            # updated_host= le.def_update_an_object(cr_obj_id= row['id'],
            #               cr_name= row['trg_name'],
            #               cr_parent= df_result_sql_parent['id'].values[0],
            #               cr_prop=prop) #to update tags from properties if needed


#0.Метрики работы с объектами для вывода результатов работы модуля

objects_in_tree = 0
objects_created = 0
objects_updated = 0
errors_commited = 0

cloned_obj = []

#1. Загрузка таблицы csv для изменения свойств из форматированного файла
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
          :-3] + ' --- 1. Загрузка таблицы csv для изменения свойств из форматированного файла')
else:
    ll.print_log.info(' --- 1. Загрузка таблицы csv для именения свойств из форматированного файла')

#####os.chdir(ls.config["folders"]["working_path"])
os.chdir('C:\\Users\kruts\OneDrive\Desktop\PythonProject\saymon-scripts\\Unit_Bulk_Operations')#####
print(os.getcwd())
try:
    df_rsm_bulk = pd.read_csv(ls.cmdb_file, header=0, delimiter=';')
except Exception as e:
    print(f"Произошла ошибка при загрузке файла: {e}")

#2. Загружаем существующие группы сервисов (имена объектов)
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
          :-3] + ' --- 2. Загружаем существующие группы сервисов (имена объектов)')
else:
    ll.print_log.info(' --- 2. Загружаем существующие группы сервисов (имена объектов)')
def_refresh_objects()

#3. Совмещаем таблички - целевую и существующую, перебор и создание всех отсутствующих
    # групп сервисов под указанным существующим имененем объекта
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
          :-3] + ' --- 3. Перебор и создание всех отсутствующих групп сервисов')
else:
    ll.print_log.info(' --- 3. Перебор и создание всех отсутствующих групп сервисов')
def_create_group_services()

#4. Загружаем существующие сервисы и группы сервисов (имена объектов) с учетом вновь созданных
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
          :-3] + ' --- 4. Загружаем существующие группы сервисов (имена объектов)')
else:
    ll.print_log.info(' --- 4. Загружаем существующие группы сервисов (имена объектов)')
def_refresh_objects()

#5. Совмещаем таблички - целевую и существующую, перебор и создание всех отсутствующих
# сервисов и их свойств ("service* & serv_prop") под указанным существующим имененем объекта
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
          :-3] + ' --- 5. Перебор и создание отсутствующих сервисов и их свойств')
else:
    ll.print_log.info(' --- --- 5. Перебор и создание отсутствующих сервисов и их свойств')
def_create_services()

#6. Обновляем существующие сервисы и группы сервисов (имена объектов) с учетом вновь созданных
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[
            :-3] + ' --- 6. Загружаем существующие группы сервисов (имена объектов)')
else:
    ll.print_log.info(' --- 6. Загружаем существующие группы сервисов (имена объектов)')
def_refresh_objects()

#7&8. Если упорядочиваем Auto Ping Discovered Хосты (отладить)
def_auto_ping_discovered_hosts()

# Проверка наличия флага just_check в объекте ls. Если флаг установлен, выполняется вывод в стандартный вывод.
if ls.just_check:
    # Вывод текущей даты и времени в определенном формате, с точностью до миллисекунды, с последующим обрезанием до миллисекунд.
    # Сообщение о процессе поиска хостов и создании записей для ненайденных хостов.
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- 9. Поиск по имени хостов. Создаем по списку, что не обнаружилось. Результат в ./reports/host_added.csv')
else:
    # Аналогичное логирование, но через систему логирования для более структурированного хранения логов.
    ll.print_log.info(' --- 9. Поиск по имени хостов. Создаем по списку, что не обнаружилось. Результат в ./reports/host_added.csv')

# Формирование SQL запроса для объединения данных из двух таблиц.
query = f"SELECT full.id, "\
        f"       full.name, "\
        f"       full.child_ids, "\
        f"       rsm.* "\
        f"FROM df_rsm_bulk as rsm "\
        f"LEFT JOIN df_obj_tree as full "\
        f"ON full.name = rsm.`serv_prop:00. РСМ.Хост`"  # LEFT JOIN выполняет левостороннее соединение таблиц df_rsm_bulk и df_obj_tree,
                                                        # где ключ соединения - это соответствие между полем name таблицы full и полем `serv_prop:00. РСМ.Хост` в таблице rsm.

# Выполнение SQL запроса через функцию sqldf, которая позволяет обрабатывать SQL запросы непосредственно на объектах DataFrame.
df_result_sql = sqldf(query)

# Сохранение результата запроса в файл формата CSV.
df_result_sql.to_csv('./reports/host_added.csv')  # Запись данных в файл, путь к которому указан, для последующего анализа или отчетности.

# Итерация по строкам DataFrame df_result_sql, где каждая строка содержит информацию о хосте.
for index, row in df_result_sql.iterrows():

    # Получение значения поля 'serv_prop:00. РСМ.Хост', приведение к верхнему регистру первых пяти символов для определения локации.
    location = str(row['serv_prop:00. РСМ.Хост'])[:5].upper()

    # SQL запрос для поиска уникального идентификатора сервиса, связанного с хостом.
    query = f"SELECT DISTINCT full.id "\
            f"FROM df_obj_tree as full "\
            f"WHERE full.name = '{row['service_name']}' "
    df_result_sql_parent = sqldf(query)

    # SQL запрос для поиска графического объекта хоста.
    query = f"SELECT DISTINCT full.id "\
            f"FROM df_obj_tree as full "\
            f"WHERE full.name = '{'_'+row['serv_prop:00. РСМ.Хост']}'"
    df_result_sql_graph_host = sqldf(query)

    # Определение, связан ли хост с графическим объектом или только с сервисом.
    if not(df_result_sql_graph_host.empty):
        host_id_first_parent = df_result_sql_graph_host['id'][0]
        graph_host_id = host_id_first_parent
    elif not(df_result_sql_parent.empty):
        host_id_first_parent = df_result_sql_parent['id'][0]
    elif ls.just_check:
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- 9a. Тестовый прогон. Сервисы не созданы')

    prop = []
    df_serv_properties = df_rsm_bulk.filter(regex=(r"(prop:)"))  # Извлечение свойств хоста в отдельный DataFrame.

    # Сбор свойств хоста для последующего использования или обработки.
    for serv_properties in df_serv_properties.columns:
        prop.append({"name": serv_properties.replace('serv_prop:', ''), "value": str(row[serv_properties]), "type_id": 1})

    # Добавление IP адреса хоста в список свойств.
    prop.append({"type_id": 1, "name": "Address", "value": str(row['serv_prop:01. IP'])})

    # Обработка ситуации, когда хост отсутствует в системе.
    if row['id'] == None:
        if ls.just_check:
            print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Try create with all props: №', row['№'], ' object: ', row['serv_prop:00. РСМ.Хост'])
            objects_created += 1
        else:
            ll.print_log.info(' --- Create: №' + str(row['№']) + ' object: ' + str(row['serv_prop:00. РСМ.Хост']))

            # Подготовка данных для клонирования хоста.
            i = 0
            properties_to_change = {'IP': '1.1.1.1'}  # Значение по умолчанию для IP, если оно отсутствует.
            name_for_clone = 'Test'  # Имя по умолчанию для клонированного объекта.

            # Поиск и замена IP адреса в свойствах хоста.
            for i in range(len(prop)):
                if ('Address' in prop[i]['name']) and (re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', prop[i]['value'])):
                    properties_to_change['IP'] = prop[i]['value']

            # Клонирование объекта с использованием заданных свойств и локации.
            cloned_obj = sheepSaymon.main(origin_object=ls.origin_object_host[location], clone_parent_object=host_id_first_parent,
                                          properties=properties_to_change, name_for_clone=row['serv_prop:00. РСМ.Хост'],
                                          class_name_stay=ls.class_name_stay)

            # Проверка успешности клонирования и обновление информации о созданных объектах.
            if cloned_obj:
                row['id'] = cloned_obj[0]['id']
                objects_created += len(cloned_obj)
            else:
                ll.print_log.info(' --- Хост ' + str(row['serv_prop:00. РСМ.Хост']) + ' не был создан по шаблону')
                errors_commited += errors_commited