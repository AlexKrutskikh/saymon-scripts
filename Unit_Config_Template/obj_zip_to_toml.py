from saymon_api_methods import SaymonApi
from models import Object
import tomli_w
import json

SAYMON_HOSTNAME = 'https://saas.saymon.info'
LOGIN = 'evgeny.s.saymon.info'
PASSWORD = 'fEIHOA7450'

ids = ['63d9a596aeae88225b6d0c80']

with SaymonApi(base_url=f'{SAYMON_HOSTNAME}/node/api', user=LOGIN, password=PASSWORD) as api:
    for id in ids:
        """Получаем информацию об объекте"""
        object = api.get_object_by_id(id)
        object = Object(**object) if "code" not in object else " "
        print(f"GET and validation obj{id} OK")
        """Получаем информацию об условиях перехода состояний"""
        conditions = api.get_state_conditions(id)
        conditions = conditions if "code" not in conditions else " "
        print(f"GET and validation obj{id} state-conditions OK -- {conditions}")
        """Получаем информацию о правилах формирования данных"""
        rules = api.get_stat_rules(id)
        rules = rules if "code" not in rules else " "
        print(f"GET and validation obj{id} stat-rules OK -- {rules}")
        """Получаем информацию о правилах формирования данных"""
        triggers = api.get_state_triggers(id)
        triggers = triggers if "code" not in triggers else " "
        print(f"GET and validation obj{id} state-triggers OK -- {triggers}")
        """Записываем toml-файл"""
        newtoml = {"object": {
            "id": object.id if object.id is not None else " ",
            "name": object.name if object.name is not None else " ",
            "class_id": object.class_id if object.class_id is not None else " ",
            "child_ids": object.child_ids if object.child_ids is not None else " ",
            "child_link_ids": object.child_link_ids if object.child_link_ids is not None else " ",
            "child_ref_ids": object.child_ref_ids if object.child_ref_ids is not None else " ",
            "owner_id": object.owner_id if object.owner_id is not None else " ",
            "parent_id": object.parent_id if object.parent_id is not None else " ",
            "discovery_id": object.discovery_id if object.discovery_id is not None else " ",
            "properties": object.properties if object.properties is not None else " ",
            "client_data": object.client_data if object.client_data is not None else " ",
            "state_id": object.state_id if object.state_id is not None else " ",
            "tags": object.tags if object.tags is not None else " ",
            "background": object.background if object.background is not None else " ",
            "created": object.created if object.created is not None else " ",
            "geoposition": object.geoposition if object.geoposition is not None else " ",
            "geopositionRadius": object.geopositionRadius if object.geopositionRadius is not None else " ",
            "last_state_update": object.last_state_update if object.last_state_update is not None else " ",
            "manual_state": object.manual_state if object.manual_state is not None else " ",
            "operations": str(object.operations) if object.operations is not None else " ",
            "updated": object.updated if object.updated is not None else " ",
            "weight": object.weight if object.weight is not None else " "},
            "state-conditions": {"conditions": str(conditions)},
            "stat-rules": {"rules": str(rules)},
            "state-triggers": {"triggers": triggers}}

        with open(f"dumped_objects/{object.id}.toml", "wb") as f:
            tomli_w.dump(newtoml, f)
