import httpx

from app.core.config import settings

class KeitaroClient:
    def __init__(self):
        self.base_url = settings.keitaro_base_url.rstrip("/")
        self.headers = {
            "Api-Key": settings.keitaro_api_key,
        }

    async def get(self, endpoint: str, params: dict | None = None):
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0
        ) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()

            return response.json()

    async def post(self, endpoint: str, data: dict):
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        ) as client:
            response = await client.post(endpoint, json=data)
            response.raise_for_status()

            return response.json()

    async def put(self, endpoint: str, data: dict):
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        ) as client:
            response = await client.put(endpoint, json=data)
            response.raise_for_status()

            return response.json()

    async def delete(self, endpoint: str):
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        ) as client:
            response = await client.delete(endpoint)
            response.raise_for_status()

            return response.json()