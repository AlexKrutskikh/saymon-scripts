#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to run in docker:
#docker run --rm -v /opt/saymon-scripts/laim/Unit_Bulk_Operations/:/opt/saymon-scripts/laim/Unit_Bulk_Operations -v /var/log/saymon/laim/:/var/log/saymon/laim laim-docker-rnn python3 /opt/saymon-scripts/laim/Unit_Bulk_Operations/laim_gpn_bulk_changes.py $object_id $metrics_name

import sys
import warnings
warnings.filterwarnings("ignore")

import json
import requests
import time, os
from datetime import datetime, timezone

import pandas as pd
import datetime as DT
#import numpy as np
from pandasql import sqldf
import re

################### Выбрать требуемый конфиг и рабочая папка #######
import laim_session_config_gpn as ls
####################################################################

#import sheepSaymon
import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)
import laim_import_saymon_api as li
import laim_export_saymon_api as le

from def_gpn_bulk import def_refresh_objects, def_create_group_services,def_create_services, def_custom_oms_VM_pin, def_custom_msk_VM_pin, def_custom_vm_pin, def_auto_ping_discovered_hosts

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
df_rsm_bulk = pd.read_csv(ls.cmdb_file, header = 0, delimiter=';')
print(df_rsm_bulk)

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

# Обновление свойств и клиентских данных для существующего или новосозданного объекта.
# В случае тестового запуска, проверка свойств вынесена за пределы SDK.
if ls.just_check:
    # Инициализация списков для существующих и новых свойств.
    prop_exist = list()
    prop_new = list()
    # Получение свойств объекта.
    obj_properties = li.get_object_properties(row['id'])
    # Проверка, если свойства найдены и объект существует.
    if 'NotFound' not in str(obj_properties):
        # Разделение свойств на новые и существующие.
        for i in range(len(prop)):
            compare_prop = list(filter(lambda item: item['name'] == prop[i]['name'], obj_properties['properties']))
            if compare_prop:
                prop[i]['id'] = compare_prop[0]['id']
                prop_exist.append(prop[i])
            else:
                prop_new.append(prop[i])
        # Проверка изменения значений существующих свойств.
        for data_r in prop_exist:
            compare_prop = list(filter(lambda item: item['name'] == data_r['name'] and item['value'] == data_r['value'], obj_properties['properties']))
            if not compare_prop:
                prop_id = data_r['id']  # Получение идентификатора свойства для возможного обновления.

        # Вывод информации о новых и обновленных свойствах хоста.
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Хост: ' + row['serv_prop:00. РСМ.Хост'] + ' New Properties:' + str(prop_new))
        print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Хост: ' + row['serv_prop:00. РСМ.Хост'] + ' Properties with new value:' + str(compare_prop))
else:
    # Логика определения иерархии вложенных объектов и видов хостов в зависимости от местоположения и типа.
    dashboard_host = li.def_search_anything({
        "search": {"name": ls.dashboard_host_prefix[location][str(row['serv_prop:04. Тип хоста'])] + row['serv_prop:00. РСМ.Хост'], "parent_id": host_id_first_parent},
        "options": {"includeClientData": "true"}
    })
    if dashboard_host:
        dashboard_host = dashboard_host[0]['id']
    else:
        ll.print_log.info(' --- У объекта : ' + str(row['serv_prop:00. РСМ.Хост']) + ' отсутствует дашборд с префиксом:' + ls.dashboard_host_prefix[location][str(row['serv_prop:04. Тип хоста'])] + ". Ошибка: " + str(err))

    # Добавление ссылки на дашборд в свойства хоста.
    prop.append({'name': 'Перейти на дашборд ' + str(row['serv_prop:00. РСМ.Хост']), 'type_id': 6, 'value': ls.url + '/#objects/' + str(dashboard_host) + '/standard'})

    try:
        # Обновление свойств объекта в зависимости от режима коррекции.
        if ls.every_day_correction_mode:
            updated_obj = le.def_update_an_object(cr_obj_id=row['id'], cr_parent=None, cr_name=None, cr_prop=prop, cr_tag_id=None)
        else:
            updated_obj = le.def_patch_all_properties(row['id'], prop)

        if updated_obj and updated_obj['id'] != '':
            ll.print_log.info(' --- Обновлены свойства объекта: №' + str(row['№']) + ' ' + str(row['serv_prop:00. РСМ.Хост']))
            objects_updated += 1
        elif updated_obj['errors']:
            ll.print_log.info(' --- Не удалось обновить все свойства объекта: №' + str(row['№']) + ' ' + str(row['serv_prop:00. РСМ.Хост']))
            errors_commited += int(updated_obj['errors'])
    except Exception as err:
        ll.print_log.info(' --- Объект : ' + str(row['serv_prop:00. РСМ.Хост']) + ' не создан, обновить свойства не удается: ' + str(err))
        errors_commited += 1

    # Дополнительная логика по обновлению графических порогов и добавлению метрик в подобъекты и дашборды хоста.
    for i in row.index:
        if 'serv_prop:11.' in i and 'serv_prop:11. ' not in i:
            graph_thr_2add = i.replace('serv_prop:', '').split('.')[3].lstrip().replace(':', ',')  # Обработка названий метрик.
            part_name_to_add_threshold = graph_thr_2add.split(',')[0].lstrip() + ":"
            graph_value = row[i]
            dpayload = {graph_thr_2add: graph_value}
            subobjects_with_metrics = li.def_search_anything({
                "search": {"name": {"$regex": "^" + part_name_to_add_threshold + ".*$", "$options": "i"}, "parent_id": str(row['id'])},
                "options": {"includeClientData": "true"}
            })
            if subobjects_with_metrics:
                le.def_push_stat_rules(str(subobjects_with_metrics[0]['id']), [{"actions": [{"type": "extend"}]}])
                le.def_push_data(object_id=str(subobjects_with_metrics[0]['id']), data_string={"timestamp": int(ls.V_UTC_TIME_NOW), "period": 60*60*1000, "payload": dpayload})
                objects_updated += 1

# БИЗНЕС ЛОГИКА! Имена объектов содержат кодовое имя площадки. Осуществляется создание графического объекта для хоста.
if ls.just_check:
    # Если режим проверки, вывод информации о попытке создания или обновления графического объекта.
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Try create/ update: №', row['№'],
          ' graph object: ', '_' + row['serv_prop:00. РСМ.Хост'])
    objects_created += 1
elif df_result_sql_graph_host.empty:
    # Если графический объект не существует, происходит его создание.
    ll.print_log.info(' --- Create: №' + str(row['№']) + ' graph object: _' + str(row['serv_prop:00. РСМ.Хост']))

    # Попытка получить конфигурацию для создания графического объекта, зависящую от локации и типа хоста.
    try:
        dashboard_parents_dict = ls.dashboard_parents_dict[location][str(row['serv_prop:04. Тип хоста'])]
    except Exception as err:
        # В случае ошибок в конфигурации выводится сообщение для проверки файла конфигурации.
        ll.print_log.info(
            ' --- Проверить config.ini и файл cmdb, не совпадает описание площадки или тип машины: ' + str(err))

    # Создание графического объекта с использованием полученной конфигурации.
    created_obj = le.def_create_an_object(cr_name='_' + row['serv_prop:00. РСМ.Хост'],
                                          cr_parent=dashboard_parents_dict, cr_class=ls.graph_VM_class_id,
                                          cr_discovery_id='_' + row['serv_prop:00. РСМ.Хост'],
                                          cr_client_data=ls.dict_class_template.get(ls.graph_VM_class_id),
                                          cr_prop=prop)
    if created_obj != []:
        # Если объект успешно создан, но ID не присвоен, производится дополнительный поиск объекта для корректного ID.
        if created_obj['id'] == '':
            created_obj = li.def_search_anything(
                {"search": {"name": {"$regex": "^_" + row['serv_prop:00. РСМ.Хост'] + "$", "$options": "i"}},
                 "options": {"includeClientData": "true"}})[0]
        objects_created += 1
    graph_host_id = created_obj['id']
    ll.print_log.info(' --- Обновляем список родителей объекта.')

    # Обновление списка родителей объекта для включения нового графического объекта.
    new_list_parent_id = le.def_get_object(str(row['id']))
    if 'parent_id' in new_list_parent_id:
        clean_list = list(new_list_parent_id['parent_id'])
    else:
        clean_list = list(df_obj_tree.loc[df_obj_tree.id == row['id'], 'parent_id'].values[0])

    # Удаление недействительных или дублирующих родителей.
    for p in new_list_parent_id:
        if (len(df_obj_tree.loc[(df_obj_tree.id == p)]) == 0) | (p == row['id']):
            clean_list.remove(p)
    clean_list.append(str(graph_host_id))
    new_list_parent_id.sort()
    clean_list.sort()

    # Проверка на изменения в списке родителей и обновление при необходимости.
    if new_list_parent_id != clean_list:
        new_list_parent_id = clean_list
        for i in range(2):  # Две попытки с задержкой для обновления.
            updated_obj = le.def_update_an_object(cr_obj_id=row['id'], cr_parent=new_list_parent_id, cr_name=None,
                                                  cr_prop=None, cr_tag_id=None)
            if updated_obj is None:
                pass
            elif updated_obj['errors'] != 0:
                ll.print_log.info(' --- Не удалось обновить все свойства объекта: №' + str(row['№']) + ' ' + str(
                    row['serv_prop:00. РСМ.Хост']))
                errors_commited += int(updated_obj['errors'])
            elif updated_obj['id'] != '':
                objects_updated += 1
                break
            time.sleep(0.5)  # Пауза между попытками.

# Обновление графического объекта
if not ls.just_check:
    try:
        # Выбор метода обновления в зависимости от режима работы
        if ls.every_day_correction_mode:
            # Ежедневное обновление объекта с передачей только измененных свойств
            updated_obj = le.def_update_an_object(cr_obj_id=graph_host_id, cr_parent=None, cr_name=None, cr_prop=prop, cr_tag_id=None)
        else:
            # Полное обновление свойств объекта, что может затронуть историю изменений
            updated_obj = le.def_patch_all_properties(graph_host_id, prop)

        # Обработка результатов обновления
        if updated_obj is None:
            pass  # Нет действия, если объект не возвращает ошибки или данные
        elif updated_obj['id'] != '':
            # Логирование успешного обновления
            ll.print_log.info(' --- Обновлены свойства объекта: №' + str(row['№']) + ' _' + str(row['serv_prop:00. РСМ.Хост']))
            objects_updated += 1
        elif updated_obj['errors'] != 0:
            # Логирование ошибок при обновлении
            ll.print_log.info(' --- Не удалось обновить все свойства объекта: №' + str(row['№']) + ' ' + str(row['serv_prop:00. РСМ.Хост']))
            errors_commited += int(updated_obj['errors'])
    except Exception as err:
        # Логирование исключений, если обновление не может быть выполнено
        ll.print_log.info(' --- Объект : _' + str(row['serv_prop:00. РСМ.Хост']) + ' не создан, обновить свойства не удается: ' + str(err))
        errors_commited += 1

# Бизнес-логика для обновления IP адреса объекта
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Try update IP address for clone №' + str(row['№']))
    objects_updated += 1
else:
    # Поиск объекта Ping по регулярному выражению и его родителю
    ping_ip = li.def_search_anything({
        "search": {"name": {"$regex": "^.*$", "$options": "i"}, "parent_id": str(row['id'])},
        "options": {"includeClientData": "true"}
    })
    ping_prop = []
    # Проверка и замена IP адреса, если отличается от текущего
    for i in range(len(ping_ip[0]['properties'])):
        if 'PingHost' in ping_ip[0]['properties'][i]['name'] and (re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ping_ip[0]['properties'][i]['value'])) != row['serv_prop:01. IP']:
            ping_ip[0]['properties'][i]['value'] = row['serv_prop:01. IP']
            ping_prop.append(ping_ip[0]['properties'][i])

    # Обновление свойств объекта Ping с новым IP
    try:
        updated_obj = le.def_update_an_object(cr_obj_id=ping_ip[0]['id'], cr_parent=None, cr_name=None, cr_prop=ping_prop, cr_tag_id=None)
        if updated_obj is None:
            pass  # Нет действия, если объект не возвращает ошибки или данные
        elif updated_obj['id'] != '':
            ll.print_log.info(' --- Обновлены свойства объекта: №' + str(row['№']) + ' _' + str(row['serv_prop:00. РСМ.Хост']))
            objects_updated += 1
        elif updated_obj['errors'] != 0:
            ll.print_log.info(' --- Не удалось обновить все свойства объекта: №' + str(row['№']) + ' ' + str(row['serv_prop:00. РСМ.Хост']))
            errors_commited += int(updated_obj['errors'])
    except Exception as err:
        ll.print_log.info(' --- Объект : _' + str(row['serv_prop:00. РСМ.Хост']) + ' не создан, обновить свойства не удается: ' + str(err))
        errors_commited += 1



# Бизнес-логика: проверка и замена ID эталонного объекта на ID клона.
if ls.just_check:
    # Вывод сообщения о тестовой операции обновления ID клона.
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Try update ID for clone №' + str(row['№']))
    objects_updated += 1
else:
    # Обход списка клонированных объектов для обновления их данных.
    for list_row_ext in range(len(cloned_obj)):
        new_object = le.def_get_object(cloned_obj[list_row_ext]['id'])
        for list_row_int in range(len(cloned_obj)):
            if cloned_obj[list_row_int]['id_origin'] in str(new_object):
                # Обновление client_data и properties нового объекта с новыми ID.
                if cloned_obj[list_row_int]['id_origin'] in str(new_object['client_data']):
                    new_object['client_data'] = str(new_object['client_data']).replace(cloned_obj[list_row_int]['id_origin'], cloned_obj[list_row_int]['id'])
                if cloned_obj[list_row_int]['id_origin'] in str(new_object['properties']):
                    new_object['properties'] = json.loads(str(new_object['properties']).replace(cloned_obj[list_row_int]['id_origin'], cloned_obj[list_row_int]['id']).replace('\'','\"'))
                try:
                    updated_obj = le.def_update_an_object(cr_obj_id=new_object['id'], cr_client_data=new_object['client_data'], cr_prop=new_object['properties'])
                    if updated_obj is None:
                        pass
                    elif updated_obj['id'] != '':
                        ll.print_log.info(' --- Обновлены свойства объекта: №' + str(row['№']) + ' _' + str(row['serv_prop:00. РСМ.Хост']))
                        objects_updated += 1
                    elif updated_obj['errors'] != 0:
                        ll.print_log.info(' --- Не удалось обновить все свойства объекта: №' + str(row['№']) + ' ' + str(row['serv_prop:00. РСМ.Хост']))
                        errors_commited += int(updated_obj['errors'])
                except Exception as err:
                    ll.print_log.info(' --- Объект : _' + str(row['serv_prop:00. РСМ.Хост']) + ' не создан, обновить свойства не удается: ' + str(err))
                    errors_commited += 1

# Обновление дерева объектов в зависимости от режима проверки.
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- 9a. Загружаем существующие группы сервисов (имена объектов)')
else:
    ll.print_log.info(' --- 9a. Загружаем существующие группы сервисов (имена объектов)')
def_refresh_objects()

# Расстановка массовых объектов на виде в зависимости от площадки.
def_custom_VM_pin('MSK05')
def_custom_VM_pin('OMS02')

# Отчет о выполнении автосверки CMDB.
if ls.just_check:
    print(datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + ' --- Автосверка CMDB выполнена без применения на инфраструктуру')
else:
    ll.print_log.info(' --- Автосверка CMDB выполнена и применена на инфраструктуре')

# Сбор результатов операций.
result = []
result.append({"Обновлено": datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[:-3]})
result.append({"Объектов создано": str(objects_created)})
result.append({"Объектов обновлено": str(objects_updated)})
result.append({"Ошибок выполнения": str(errors_commited)})
print(result)

