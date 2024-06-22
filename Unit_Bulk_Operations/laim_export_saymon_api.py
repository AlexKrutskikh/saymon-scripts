#!/usr/bin/python3 

#%% Jupiter main
import os

import requests
import json
import re

import laim_logging as ll
ll.logging.config.dictConfig(ll.DEFAULT_LOGGING)
################### Выбрать требуемый конфиг #######################
import laim_session_config_gpn as ls
####################################################################
from Unit_Bulk_Operations import laim_import_saymon_api as li
from requests.auth import HTTPBasicAuth

expire_period = 10*60*1000 #10 minutes
force_create = 1
objects_cache = []

ll.print_log.info(" - exporter initiated")

###
#to remove some special symbols from file names
def clear_name(docname,
                slash_replace='-',  # слэш: заменять на минус; используется в идентификаторах документов: типа № 1/2
                quote_replace='',  # кавычки: замены нет - удаляем
                multispaces_replace='\x20', # множественные пробелы на один пробел
                quotes="""“”«»'\""""  # какие кавычки будут удаляться
                ):
    docname = re.sub(r'[' + quotes + ']', quote_replace, docname)
    docname = re.sub(r'[/]', slash_replace, docname)
    docname = re.sub(r'[|*?<>:\\\n\r\t\v]', '', docname)  # запрещенные символы в windows
    docname = re.sub(r'\s{2,}', multispaces_replace, docname)
    docname = docname.strip()
    docname = docname.rstrip('-') # на всякий случай
    docname = docname.rstrip('.') # точка в конце не разрешена в windows
    docname = docname.strip()    # не разрешен пробел в конце в windows
    return docname
###---

###
def def_load_document_to_repo(folder: str, file_name: str, object_repo_id: str):
    files = {
        'file': (
            file_name,
            open(folder+clear_name(file_name), mode='rb'),
            'application/pdf'
        )
    }
# loading file to common repository 
    load_doc_response = requests.request(
        'POST', ls.url + '/node/api/objects/' + ls.download_repo_id + '/docs' + ls.auth, files=files).json()
    report_link = '/node-resources/docs/uid/' + load_doc_response['value'] + '/pdf/1.pdf'

# link to download from repository, clear_name to remove some special symbols from file names
    download_params = {'name': 'Скачать: объект '+ object_repo_id + '/' + clear_name(file_name),  'value': report_link, 'type_id': 6}
    requests.request(
        'PATCH', ls.url + '/node/api/objects/' + ls.download_repo_id + '/props/'+ load_doc_response['id'] + ls.auth, json=download_params).json()    

# copy link to object documents repository        
    doc_params = {'name': 'Просмотреть ' + clear_name(file_name), 'type_id': 6, 'value': report_link}
    requests.request(
        'POST', ls.url + '/node/api/objects/' + object_repo_id + '/docs' + ls.auth, json=doc_params).json()

    ls.print_log.info(clear_name(file_name)[:-4] + ' сгенерирован.')
    if not ls.test_CLI:
        os.remove(folder+ clear_name(file_name))
###---
###
def def_check_tag(tag_name):
	run = requests.request(
				method='get',
				url=ls.url+'/node/api/tags',
				auth= ls.auth,
				verify=False).json()
	try:
		for item in run:
			if str(item['name']) == str(tag_name): 
				return item['id']
	except:
		return		
### ---
###
def def_add_tag(tag_name):

	already_tag = def_check_tag(tag_name)
	if already_tag: return already_tag

	data = {}
	data['name']       = tag_name
	run = requests.request(
				method='post',
				url=ls.url+'/node/api/tags',
				json=data,
				auth=ls.auth_token,
				verify=False).json()
	try:
		return run['id']
	except (KeyError):
		return	
### ---
###
def def_get_object(object_id):
    response = requests.request(
        method = 'get',
        url    = ls.url+'/node/api/objects/'+object_id+ ls.auth,
        verify=False
    ).json()
    return response
### ---
###
def def_add_object_parent(object_id,extra_parent):
    ll.print_log.debug('')
    ll.print_log.debug('....add_object_parent - object_id '+ object_id+ ' , extra_parent - '+ extra_parent)

    got_object = def_get_object(object_id)
    try:
        ll.print_log.debug('....add_object_parent - got_object - parent_id '+ str(got_object['parent_id']))
    except (KeyError):
        ll.print_log.debug('....add_object_parent - got_object - there is no parent_id') 
        return

    if extra_parent in got_object['parent_id']:
        pass
    else:
        if len(got_object['parent_id'][0]) == 24:  ## do not add to 1 ever
            got_object['parent_id'].append(extra_parent)
            ll.print_log.debug('....add_object_parent - new parent_id is ' + str(got_object['parent_id']))
            run = requests.request(
                method='patch',
                url=ls.url+'/node/api/objects/'+object_id,
                json={"parent_id":got_object['parent_id']},
                auth = ls.auth_token,
                verify=False
            ).json()
            ll.print_log.debug('')
### ---
###
def def_add_conditions(object_id,string):
    run = requests.request(
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'},
        method='put',
        url=ls.url+'/node/api/objects/'+object_id+'/state-conditions',
        data=ls.json.dumps(string),
        auth = ls.auth_token,
        verify=False
    )
    ll.print_log.debug('....add_conditions result is '+ str(run))
### ---
###
def def_add_property(object_id,string):
    run = requests.request(
        method='post',
        url=ls.url+'/node/api/objects/'+object_id+'/props',
        json=string,
        auth = ls.auth_token,
        verify=False
    ).json()
    ll.print_log.debug('....add_property result is '+ str(run))
### ---
###
def def_patch_class_client_data(object_id,cr_client_data):
#erase all properties!!!
    data = {}
    data["client_data"] = cr_client_data
    run = requests.request(
        method='patch',
        url=ls.url+'/node/api/objects/'+object_id+ ls.auth,
        json=data,
        verify=False
    ).json()
    ll.print_log.debug('....add_property result is '+ str(run))
### ---
###
def def_patch_all_properties(object_id,cr_prop):
#erase all properties!!!
    data = {}
    data["properties"] = cr_prop
    run = requests.request(
        method='patch',
        url=ls.url+'/node/api/objects/'+object_id+ ls.auth,
        json=data,
        verify=False
    ).json()
    ll.print_log.debug('....add_property result is '+ str(run))
### ---
###
def def_push_data(object_id,data_string):
    run = requests.request(
                method='post',
                url= ls.url+'/node/api/objects/'+object_id+'/stat'+ ls.auth,
                headers= {'Content-Type': 'application/json'},
                data=json.dumps(data_string),
                verify=False)    
    return run
### ---
###
def def_push_stat_rules(object_id,data_string):
    run = requests.request(
                method='put',
                url= ls.url+'/node/api/objects/'+object_id+'/stat-rules'+ ls.auth,
                headers= {'Content-Type': 'application/json'},
                data=json.dumps(data_string),
                verify=False)   
    if run.ok: 
        return run
    else: print(run.text)
### ---
###
def def_push_stat_to_laim(object_id,data_string,object_name = ''): #доделать универсальную процедуру, вынести переменные из бизнес логики!
    #find laim child object
    #работать будем с метриками объекта прогнозирования, а графики нарисуем в основной объект через client_id
    laim_object = li.def_search_anything({"search": {"name": {"$regex": "^Аналитика..*$","$options": "i"},
                            "parent_id": object_id},"options":{"includeClientData": "true"}})
    if laim_object == []:
        laim_object = def_create_an_object(cr_name = 'Аналитика. '+ object_name, cr_discovery_id = 'tech_'+ object_id+'_'+
                                              'Аналитика_'+ object_name, cr_parent = object_id, cr_class = 24)    
        run = def_push_stat_rules(laim_object['id'], [{"actions":[{"type": "extend"}]}])
        run = requests.request(
                method='post',
                url= ls.url+'/node/api/objects/'+laim_object['id']+'/stat'+ ls.auth,
                headers= {'Content-Type': 'application/json'},
                data=json.dumps(data_string),
                verify=False) 
        laim_object_id = laim_object['id']
    else:
        run = def_push_stat_rules(laim_object[0]['id'], [{"actions":[{"type": "extend"}]}])
        #run = def_push_stat_rules(laim_object[0]['id'], [])
        run = requests.request(
        method='post',
        url= ls.url+'/node/api/objects/'+laim_object[0]['id']+'/stat'+ ls.auth,
        headers= {'Content-Type': 'application/json'},
        data=json.dumps(data_string),
        verify=False)     
        laim_object_id = laim_object[0]['id']
    if run.ok: 
        return run, laim_object, laim_object_id
    else: print(run.text) 
### ---
###
def def_set_state(object_id,state_id,string):
	data_string = {"stateId":state_id,"reason":string,"since":int(ls.time.time() * 1000),"until":int(ls.time.time() * 1000)+expire_period}
	run = requests.request(
				method='put',
				url=ls.url+'/node/api/objects/'+object_id+'/manual-state',
				json=data_string,
				auth = ls.auth_token,
				verify=False)    	
### ---
###
def def_search_discovery_id(pattern):

    ## check cache before go further , return if found
    for object_one in objects_cache:
        if object_one['discovery_id'] == pattern: return object_one 

    ## if not cached go to search on server
    data = {"search":{"discovery_id":{"$regex":"^"+str(pattern)+"$"}}} #{search: {parent_id: "6321aafd6ba63b5693ddbd77"}, options: {includeClientData: true}}
    try:
        response = requests.request(
        'post', ls.url+'/node/api/objects/search' + ls.auth, json=data, verify=False).json()

        try:
            objects_cache.append({"name":response[0]['name'],"discovery_id":response[0]['discovery_id'],"id":response[0]['id'],"properties":response[0]['properties']})
            return {"name":response[0]['name'],"discovery_id":response[0]['discovery_id'],"id":response[0]['id'],"properties":response[0]['properties']}
        except IndexError:
            return {}
    except requests.exceptions.RequestException as e:
        return {}
### ---
###
def def_create_an_object(cr_name, cr_parent, cr_discovery_id= None, cr_child= None, cr_prop= None, cr_tag_id= None, cr_class= None, cr_client_data= None, cr_background= None):
    data = {}
    if cr_name !=           None: data['name']         = cr_name
    if cr_parent !=         None: data['parent_id']    = cr_parent
    if cr_child !=          None: data['child_id']    = cr_child
    if cr_class !=          None: data['class_id']     = cr_class
    if cr_discovery_id !=   None: data['discovery_id'] = cr_discovery_id
    if cr_client_data !=    None: data['client_data']  = cr_client_data
    if cr_tag_id !=         None: data['tags']         = cr_tag_id
    if cr_background !=     None: data['background']   = cr_background
    if cr_prop !=           None: data['properties']= cr_prop


    ll.print_log.debug('.....create_an_object - go to create with data - '+ls.url+'/node/api/objects')

    try:
        response = requests.post(
            f"{ls.url}/node/api/objects",
            json=data,
            auth=HTTPBasicAuth('admin', 'saymon')
        )
        response = response.json()
        ll.print_log.debug('.....create_an_object - object created:' + str(response))

        try:
            ll.print_log.debug('.....create_an_object - '+ str({"name":response['name'],"id":response['id']}))
            return {"name":response['name'],"id":response['id'], "properties":response['properties']}
        except (IndexError,KeyError):
            ll.print_log.debug('.....create_an_object - error 1: '+ str(response))
            return {"id":""}
    except requests.exceptions.RequestException as e:
        ll.print_log.debug('.....create_an_object - error 2: '+ str(e))
        return {"id":""}
### ---
###
def def_compare_object_properties(cr_obj_id,cr_prop= None):
    data = {}
    if cr_prop != None: data['properties'] = cr_prop
    response = None
    errors = 0
    prop_exist= list()
    prop_new= list()
    if cr_prop!= None:
#проверяем наличие свойств и делим на два массива - новые и существующие
        obj_properties = li.get_object_properties(cr_obj_id)
    prop_exist= list()
    prop_new= list()
    if cr_prop!= None:
#проверяем наличие свойств и делим на два массива - новые и существующие
        obj_properties = li.get_object_properties(cr_obj_id)
        for i in range(len(cr_prop)):
            compare_prop = list(filter((lambda item: item['name'] == cr_prop[i]['name']), obj_properties['properties']))
            if compare_prop != []:
                cr_prop[i]['id'] = (compare_prop[0]['id'])
                prop_exist.append(cr_prop[i])
            else: 
                prop_new.append(cr_prop[i])
#создаем новые свойства prop. type_id обязателен!
        data['properties'] = prop_new
        for data_r in data['properties']:
                ll.print_log.debug(
                    ' --- new properties ' + str(data_r))
#обновляем существующие свойства prop
        data['properties'] = prop_exist
        for data_r in data['properties']:
            compare_prop = list(filter((lambda item: (item['name'] == data_r['name']) and (
                item['value'] == data_r['value'])), obj_properties['properties']))
            if compare_prop == []:
                prop_id = data_r['id'] #разделяем json и id свойства
                del data_r['id']
    return {"new_property": prop_new, "exists_with_new_value":prop_exist}
### ---
###
def def_update_an_object(cr_obj_id,cr_parent=None,cr_name= None,cr_prop= None,cr_tag_id= None,cr_client_data= None):
    data = {}
    if cr_name !=           None: data['name']         = cr_name
    if cr_parent !=         None: data['parent_id']    = cr_parent
    if cr_tag_id !=         None: data['tags']         = cr_tag_id
    if cr_prop !=           None: data['properties']   = cr_prop
    if cr_client_data !=    None: data['client_data']  = cr_client_data

#для редких массовых заливок можно включать спец таг 'new' - посмотреть id
#    data['tags'] = ['645e8e7e83a021c98e52fae6']

    response = None
    errors = 0
    prop_exist= list()
    prop_new= list()
    if cr_prop!= None:
#проверяем наличие свойств и делим на два массива - новые и существующие
        obj_properties = li.get_object_properties(cr_obj_id)
        for i in range(len(cr_prop)):
            compare_prop = list(filter((lambda item: item['name'] == cr_prop[i]['name']), obj_properties['properties']))
            if compare_prop != []:
                cr_prop[i]['id'] = (compare_prop[0]['id'])
                prop_exist.append(cr_prop[i])
            else: 
                prop_new.append(cr_prop[i])
#создаем новые свойства prop. type_id обязателен! Value свойства всегда String!
        data['properties'] = prop_new
        for data_r in data['properties']:
            try:
                response = requests.request(
                    'post', ls.url+'/node/api/objects/' + cr_obj_id + '/props' + ls.auth, json=data_r, verify=False).json()
                ll.print_log.debug(
                    ' --- Object properties created ' + str(response))
            except requests.exceptions.RequestException as e:
                ll.print_log.debug(' --- Update_an_object - error 2: '+ str(e))
                errors = errors+1
#обновляем существующие свойства prop
        data['properties'] = prop_exist
        for data_r in data['properties']:
            compare_prop = list(filter((lambda item: (item['name'] == data_r['name']) and (
                item['value'] == data_r['value'])), obj_properties['properties']))
            if compare_prop == []:
                prop_id = data_r['id'] #разделяем json и id свойства
                del data_r['id']
                #Перебираем строки в obj_propeties и проверяем равенство значений
                try:
                    response = requests.request(
                                'patch', ls.url+'/node/api/objects/'+ cr_obj_id + '/props/'+ prop_id + 
                                ls.auth, json= data_r, verify=False).json()
                    ll.print_log.debug(' --- Object properties updated '+ str(response))
                except requests.exceptions.RequestException as e:
                    ll.print_log.debug(' --- Update_an_object - error 2: '+ str(e))
                    errors = errors+1
        del data['properties'] #убираем свойства из словаря
#обновляем базовые поля объекта 
    if cr_client_data!= None:    
        obj_base_fields = def_get_object(cr_obj_id)
#обновляем client_data модификация только при отсутствии или различии  
        data_c = {}
        data_c['client_data'] = data['client_data']
        if 'client_data' in obj_base_fields:
            if data['client_data'] != obj_base_fields['client_data']:
                try:            
                    response = requests.request(
                    'patch', ls.url+'/node/api/objects/'+ cr_obj_id + ls.auth, json= data_c, verify=False).json()
                    ll.print_log.debug(' --- Object client data updated ')
                except requests.exceptions.RequestException as e:
                    ll.print_log.debug(' --- Update_an_object - error 2: '+ str(e))
                    errors = errors+1
        else:
            try:            
                response = requests.request(
                'patch', ls.url+'/node/api/objects/'+ cr_obj_id + ls.auth, json= data_c, verify=False).json()
                ll.print_log.debug(' --- Object client data updated ')
            except requests.exceptions.RequestException as e:
                ll.print_log.debug(' --- Update_an_object - error 2: '+ str(e))
                errors = errors+1
        del data['client_data'] #убираем клиентские данные (позиция и z-index) из словаря
    if data != {}:
        try:
            response = requests.request(
            'patch', ls.url+'/node/api/objects/'+ cr_obj_id + ls.auth, json=data, verify=False).json()
            ll.print_log.debug(' --- Object attributes updated')
        except (IndexError,KeyError):
            ll.print_log.debug(' --- Object attributes updating error 1: '+ str(response))
            errors = errors+1
    if response != None:
        if 'ResourceNotFound' in str(response):
            ll.print_log.debug(' --- Object attributes updating error 2: '+ str(response))
        else: 
            return {"id":response['id'],"errors": errors}

### ---
###
def def_create_a_link(cr_source, cr_dest, cr_state_id, cr_prop, cr_tag_id, cr_class, cr_client_data, cr_weigth):
    data = {}
    if cr_source !=         None: data['cr_source']    = cr_source
    if cr_dest !=           None: data['cr_dest']      = cr_dest
    if cr_state_id !=       None: data['cr_state_id']  = cr_state_id
    if cr_prop !=           None: data['properties']   = cr_prop
    if cr_tag_id !=         None: data['tags']         = cr_tag_id
    if cr_class !=          None: data['class_id']     = 35
    if cr_client_data !=    None: data['client_data']  = cr_client_data
    if cr_weigth !=         None: data['cr_weigth']    = cr_weigth

    data['owner_id'] = '614cdfc72303be6914e9c5b7'

    ll.print_log.debug('.....create_an_object - go to create with data - '+ str(data))
    try:
        response = requests.request(
        'post', ls.url+'/node/api/links' + ls.auth, json=data, verify=False).json()

        ll.print_log.debug('.....create_an_object - object created:'+ str(response))
        try:
            ll.print_log.debug('.....create_an_object - '+ str({"name":response['name'],"id":response['id']}))
            return {"name":response['name'],"id":response['id']}
        except (IndexError,KeyError):
            ll.print_log.debug('.....create_an_object - error 1: '+ str(response))
            return {"id":""}
    except requests.exceptions.RequestException as e:
        ll.print_log.debug('.....create_an_object - error 2: '+ str(response))
        return {"id":""}
### ---
