import tomli
from saymon_api_methods import SaymonApi


SAYMON_HOSTNAME = 'https://saas.saymon.info'
LOGIN = 'evgeny.s.saymon.info'
PASSWORD = 'fEIHOA7450'

PATH_TO_TOML = 'dumped_objects/63d9a596aeae88225b6d0c80.toml'  # путь до дамп-файла
# критерии для поиска объектов, которые хотим обновить
# criteria = {
#     'search':
#         {
#             'id': '63ecc57e5837227e997dc241'
#         }
#     }

#criteria = {"search": {"name": {"$regex": "^MSK05\-OKD01$","$options":"i"},"options":{"includeClientData": "true"}}}

field = 'properties'
#field = 'client_data'

def update_objects_field(id, field, config, api):
    """
    Функция для обновления требуемого поля

    :param id: id объекта, который необходимо обновить
    :param field: поле, которое необходимо обновить
    :param config: тело объекта из дампа
    :return: ответ на запрос к api saymon
    """
    if field == 'properties':
        properties_list = api.get_object_by_id(object_id=id).get('properties')
        for i_property in config.get('object').get(field):
            if i_property['type_id'] == 8: 
                continue     
            for j_prop in properties_list:
                if i_property['name'] == j_prop['name'] and i_property['type_id'] == j_prop['type_id']:
                    api.update_property(object_id=id, prop_id=j_prop['id'], value={'name': i_property['name'], 'value': i_property['value'], 'type_id': i_property['type_id']})
                    break
            else:
                try:
                    api.create_property(object_id=id, value=i_property)
                except Exception as ex:
                    print(ex)
        return

    else:
        body = {
                field: config.get('object').get(field)
            }
        print(body)
        return api.update_object(id=id, field=body)             # Если значение поля в body имеет тип List, то соответствующее поле в выборке объектов не обновляется


with SaymonApi(base_url=f'{SAYMON_HOSTNAME}/node/api', user=LOGIN, password=PASSWORD) as api:
    with open(PATH_TO_TOML, "rb") as toml_file:
        config = tomli.load(toml_file)
        print(config.get('object'))

    objects_id = '63ecc57e5837227e997dc241'
    print(update_objects_field(objects_id, field, config, api))
