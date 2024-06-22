from typing import Union, List, Final
import requests
from requests.adapters import HTTPAdapter


class SaymonApi:
    """класс, предоставляет методы для работы с апи Saymon"""
    _REQUEST_TIMEOUT: Final[int] = 3.05

    def __init__(self, base_url: str, user: str, password: str) -> None:
        self._base_url = base_url
        self._session = requests.Session()
        self._session.mount(self._base_url, HTTPAdapter(max_retries=3))
        self._session.auth = (user, password)

    def get_object_by_id(self, object_id: Union[int, str]) -> dict:
        """Метод для получения объекта по id"""
        return self._get(f'objects/{object_id}')

    def get_all_objects(self) -> Union[List[dict], dict]:
        """Метод для получения всех объектов"""
        return self._get(f'objects')

    def get_state_conditions(self, object_id):
        """Метод для получения состояний-условия"""
        return self._get(url=f'objects/{object_id}/state-conditions')

    def get_state_triggers(self, object_id):
        """Метод для получения действий при смене состояний"""
        return self._get(url=f'objects/{object_id}/state-triggers')

    def get_stat_rules(self, object_id):
        """Метод для получения ПФД"""
        return self._get(url=f'objects/{object_id}/stat-rules')

    def search(self, criteria: dict) -> dict:
        """Метод для поиска объектов"""
        return self._post('/objects/search', criteria)

    def update_object(self, id, field):
        """Метод для обновления поля объекта"""
        return self._patch(url=f'/objects/{id}', body=field)

    def create_property(self, object_id: Union[int, str], value: dict) -> dict:
        """Метод для создания свойства"""
        return self._post(f'/objects/{object_id}/props', body=value)

    def update_property(self, object_id: Union[int, str], prop_id: int, value: dict) -> dict:
        """Метод для изменения свойства объекта"""
        return self._patch(f'/objects/{object_id}/props/{prop_id}', body=value)

    def _patch(self, url: str, body: dict) -> dict:
        resp = self._session.patch(f'{self._base_url}{url}', json=body, timeout=self._REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url: str, body: Union[dict, list]) -> dict:
        resp = self._session.post(f'{self._base_url}{url}', json=body, timeout=self._REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def _get(self, url: str) -> dict:
        resp = self._session.get(f'{self._base_url}/{url}', timeout=self._REQUEST_TIMEOUT)
        return resp.json()

    def _delete(self, url: str):
        resp = self._session.delete(f'{self._base_url}{url}', timeout=self._REQUEST_TIMEOUT)
        resp.raise_for_status()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
