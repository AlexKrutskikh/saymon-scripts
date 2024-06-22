#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
#%% 

import requests
from urllib.parse import urljoin
from typing import Iterable
import datetime as DT

import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)
import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)
################### Выбрать требуемый конфиг #######################
import laim_session_config_gpn as ls
####################################################################

ll.print_log.info(" - api importer initiated")

def get_object_data(id):
    # return ls.session.get(ls.url + '/node/api/objects/' + str(id),
    # params={
    #         'fields':'parent_id,name,state_id,last_state_update,client_data'
    #     }
    # ).json()

    return requests.request(
        method='get',
        url= ls.url+'/node/api/objects/' +
        str(id) + ls.auth,
        params={
            'fields':'parent_id,name,state_id,last_state_update,client_data'
        }
    ).json()

def get_all_act_incidents_user(filter=''):
    return requests.request(
        method='get',
        url= ls.url+'/node/api/incidents'+ ls.auth + filter
    ).json()

def get_object_metrics(id):
    return requests.request(
        method='get',
        url= ls.url+'/node/api/objects/' +
        str(id) + '/stat/metrics' + ls.auth
    ).json()


def get_objects_tree():
    base_url = ls.url
    endpoint = '/node/api/objects'
    url = urljoin(base_url, endpoint)

    # Замените ваш Bearer token авторизацией через имя пользователя и пароль
    username = 'admin'  # Замените на ваше имя пользователя
    password = 'saymon'  # Замените на ваш пароль

    params = {
        'fields': 'name,id,discovery_id,parent_id,state_id,child_ids,class_id'
    }

    # Делаем запрос с авторизацией Basic Auth
    response = requests.get(url, auth=(username, password), params=params)

    # Проверяем, что ответ сервера успешен
    if response.status_code == 200:
        return response.json()
    else:
        # Обработка ошибочного ответа
        response.raise_for_status()

def get_classes_list():
    return requests.request(
        method='get',
        url= ls.url + '/node/api/classes' + ls.auth
    ).json()

def get_classes_list():
    return requests.request(
        method='get',
        url= ls.url + '/node/api/classes' + ls.auth
    ).json()

def get_all_object_properties():
    return requests.request(
        method='get',
        url= ls.url + '/node/api/objects' + ls.auth,
        params={
            'fields':'id,name,properties'
        }
    ).json()

def get_object_properties(id):
    return requests.request(
        method='get',
        url= ls.url + '/node/api/objects/'+ str(id) + ls.auth,
        params={
            'fields':'name,properties'
        }
    ).json()    

def get_history(id, metrics, downsample, fromm, to, tznm):
    return requests.request(
        method='get',
        url= ls.url + '/node/api/objects/' + str(id) + '/history' + ls.auth,
        params={
            'metrics': metrics, 'from': fromm, 'to': to, 'downsample': downsample, 'timezone': tznm
        }
    ).json()

def get_stat(id):
    return requests.request(
        method='get',
        url= ls.url + '/node/api/objects/' + str(id) + '/stat' + ls.auth,
    ).json()

def get_states():
    return requests.request(
        method='get',
        url= ls.url + '/node/api/states' + ls.auth,
    ).json()

def get_state_history(id, fromm, to):
    return requests.request(
        method='get',
        url= ls.url + '/node/api/objects/' + str(id) + '/state-history' + ls.auth,
        params={
            'from': fromm, 'to': to, 'inverse': True
        }
    ).json()

def get_dps_values(history: list):
    arr = []
    for h in history:
        for dps in h['dps']:
            arr.append(dps[1])
    return arr

def get_dps_by_value(dps: list, value):
    _dps = []
    for d in dps:
        if d[1] == value:
            _dps = [d[0], d[1]]
            break
    return _dps

def add_name_in_state(states: Iterable[dict], name: str):
    for state in states:
        state['object_name'] = name
    return states

def find_state_from_history(states: Iterable[dict], stateId, timestamp):
    for i, state in enumerate(states):
        if state['stateId'] == stateId and state['timestamp'] > timestamp:
            return state;
                
###
def def_search_anything(search_for):
#    data = {"search":{str(search_for):str(pattern)}, "options":{"includeClientData":"true"}} #{search: {parent_id: "6321aafd6ba63b5693ddbd77"}, options: {includeClientData: true}}
#    data = {"search":{"parent_id":"63203c4219f4ca0024973582"}, "options": {"includeClientData":"true"}}
    data = search_for
    try:
        response = requests.request(
        'post', ls.url+'/node/api/objects/search' + ls.auth, json=data, verify=False).json()
        return response
    except Exception as e:
        ll.print_log.debug('Search_an_object error: '+ str(e))
    
### ---
