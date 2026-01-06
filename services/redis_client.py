# redis_client.py
import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")


print("Redis REST URL:", UPSTASH_REDIS_REST_URL)


class RedisCache:
    def __init__(self):
        # Fallback to in-memory cache if env vars are missing
        self._memory = {}
        self._use_memory = not (UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)
        if not self._use_memory:
            self.url = UPSTASH_REDIS_REST_URL.rstrip("/")
            self.token = UPSTASH_REDIS_REST_TOKEN
        else:
            self.url = None
            self.token = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, key: str) -> Optional[str]:
        if self._use_memory:
            return self._memory.get(key)
        try:
            r = requests.get(f"{self.url}/get/{key}", headers=self._headers(), timeout=10)
            r.raise_for_status()
            return r.json().get("result")
        except Exception as e:
            print(f"Redis Cache GET Error (Key: {key}): {str(e)}")
            return self._memory.get(key) # Fallback to memory

    def set(self, key: str, value: str) -> dict:
        if self._use_memory:
            self._memory[key] = value
            return {"result": "OK"}
        try:
            r = requests.post(
                f"{self.url}/set/{key}",
                json={"value": value},
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Redis Cache SET Error (Key: {key}): {str(e)}")
            self._memory[key] = value # Fallback to memory
            return {"result": "MEMORY_FALLBACK"}

    def exists(self, key: str) -> bool:
        if self._use_memory:
            return key in self._memory
        r = requests.get(
            f"{self.url}/exists/{key}", headers=self._headers(), timeout=30
        )
        r.raise_for_status()
        return r.json().get("result") == 1

    def delete(self, key: str) -> dict:
        """
        Delete a key. Upstash REST supports /del/{key} as a POST.
        """
        if self._use_memory:
            self._memory.pop(key, None)
            return {"result": 1}
        r = requests.post(f"{self.url}/del/{key}", headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def keys(self, pattern: str):
        """
        NOT all Upstash plans allow scan via REST. If not available you can store
        metadata of keys yourself. This function attempts a 'scan' endpoint if present.
        """
        if self._use_memory:
            # Simple prefix match for memory mode
            prefix = pattern.rstrip("*")
            return [k for k in self._memory.keys() if k.startswith(prefix)]
        r = requests.get(
            f"{self.url}/scan/{pattern}", headers=self._headers(), timeout=30
        )
        if r.status_code == 200:
            return r.json().get("result", [])
        return []


redis_cache = RedisCache()
