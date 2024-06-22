import tomli
from saymon_api_methods import SaymonApi
import requests

# Устанавливаем параметры подключения к API SAYMON
SAYMON_HOSTNAME = 'http://127.0.0.1:8080'
LOGIN = 'admin'
PASSWORD = 'saymon'

# Путь до дамп-файла объекта в формате TOML
PATH_TO_TOML = 'dumped_objects/63d9a596aeae88225b6d0c80.toml'

# Критерии для поиска объектов, которые хотим обновить
# criteria = {
#     'search':
#         {
#             'id': '63ecc57e5837227e997dc241'
#         }
#     }

#criteria = {"search": {"name": {"$regex": "^MSK05\-OKD01$","$options":"i"},"options":{"includeClientData": "true"}}}

# Указываем поле, которое необходимо обновить
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
        # Итерируемся по свойствам объекта из дампа
        for i_property in config.get('object').get(field):
            # Итерируемся по свойствам объекта, полученного из API SAYMON
            for j_prop in api.get_object_by_id(object_id=id).get('properties'):
                # Если свойство из дампа совпадает со свойством из API SAYMON по имени, значению и типу, то обновляем его
                if i_property['name'] == j_prop['name'] and i_property['value'] == j_prop['value'] and i_property['type_id'] == j_prop['type_id']:
                    api.update_property(object_id=id, prop_id=j_prop['id'], value={'name': i_property['name'], 'value': i_property['value'], 'type_id': i_property['type_id']})
                    break
            # Если свойство из дампа не найдено в объекте из API SAYMON, то создаем его
            else:
                try:
                    api.create_property(object_id=id, value=i_property)
                except Exception as ex:
                    print(ex)
        return

    else:
        # Формируем тело запроса для обновления поля
        body = {
                field: config.get('object').get(field)
            }
        print(body)
        # Обновляем поле с помощью метода API SAYMON `update_object`
        return api.update_object(id=id, field=body)             # Если значение поля в body имеет тип List, то соответствующее поле в выборке объектов не обновляется


# Устанавливаем соединение с API SAYMON
with SaymonApi(base_url=f'{SAYMON_HOSTNAME}/node/api', user=LOGIN, password=PASSWORD) as api:
    # Загружаем конфигурацию объекта из дамп-файла
    with open(PATH_TO_TOML, "rb") as toml_file:
        config = tomli.load(toml_file)
        print(config.get('object'))

    # Указываем id объекта, который необходимо обновить
    objects_id = '63ecc57e5837227e997dc241'
    # Выполняем обновление поля объекта
    print(update_objects_field(objects_id, field, config, api))

# Устанавливает параметры для подключения к системе SAYMON, включая адрес хоста, имя пользователя, пароль и путь к дамп-файлу, содержащему конфигурацию объекта.

# Определяет функцию update_objects_field, которая принимает идентификатор объекта, поле для обновления, конфигурацию объекта и экземпляр API SAYMON в качестве параметров.

# В функции update_objects_field:

# Если поле для обновления - "properties", функция перебирает свойства в конфигурации объекта и проверяет, существуют ли они уже в объекте SAYMON. Если свойство не существует, оно создается с использованием API SAYMON.

# Если поле для обновления не "properties", оно обновляется в объекте SAYMON с использованием API SAYMON.

# Устанавливает соединение с системой SAYMON с использованием предоставленных параметров.

# Загружает конфигурацию объекта из указанного дамп-файла.

# Вызывает функцию update_objects_field для обновления указанного объекта с идентификатором objects_id и поля field с использованием конфигурации объекта и экземпляра API SAYMON.

# Выводит результат операции обновления.

# В целом, этот код используется для обновления указанного поля в объекте SAYMON с использованием конфигурации, загруженной из дамп-файла. Он полезен для обновления объектов SAYMON на основе предварительно сохраненных конфигураций.