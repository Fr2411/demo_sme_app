import os

import requests


class EasyEcomApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv('API_BASE_URL', 'http://localhost/api')).rstrip('/')

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def login(self, client_id: str, username: str, password: str) -> dict:
        response = requests.post(
            self._url('/auth/login'),
            json={'client_id': client_id, 'username': username, 'password': password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_products(self, client_id: str) -> list[dict]:
        response = requests.get(self._url('/products'), params={'client_id': client_id}, timeout=10)
        response.raise_for_status()
        return response.json()

    def create_product(self, client_id: str, name: str, category: str, cost: float, price: float) -> dict:
        response = requests.post(
            self._url('/products'),
            json={'client_id': client_id, 'name': name, 'category': category or None, 'cost': cost, 'price': price},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_sales(self, client_id: str) -> list[dict]:
        response = requests.get(self._url('/sales'), params={'client_id': client_id}, timeout=10)
        response.raise_for_status()
        return response.json()

    def create_sale(self, client_id: str, product_id: int, qty: int, selling_price: float) -> dict:
        response = requests.post(
            self._url('/sales'),
            json={
                'client_id': client_id,
                'product_id': product_id,
                'qty': qty,
                'selling_price': selling_price,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
