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
            # Using command array format for consistency and robustness
            r = requests.post(
                self.url,
                json=["GET", key],
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()
            return r.json().get("result")
        except Exception as e:
            print(f"Redis Cache GET Error (Key: {key}): {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return self._memory.get(key) # Fallback to memory

    def set(self, key: str, value: str) -> dict:
        if self._use_memory:
            self._memory[key] = value
            return {"result": "OK"}
        try:
            # Upstash REST API expects a command array for POST to the base URL
            # Format: ["SET", "key", "value"]
            r = requests.post(
                self.url,
                json=["SET", key, value],
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            
            # Upstash returns {"result": "OK"} for successful SET
            return r.json()
        except Exception as e:
            print(f"Redis Cache SET Error (Key: {key}): {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            self._memory[key] = value # Fallback to memory
            return {"result": "MEMORY_FALLBACK"}

    def exists(self, key: str) -> bool:
        if self._use_memory:
            return key in self._memory
        try:
            r = requests.post(
                self.url,
                json=["EXISTS", key],
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()
            return r.json().get("result") == 1
        except Exception as e:
            print(f"Redis Cache EXISTS Error (Key: {key}): {str(e)}")
            return key in self._memory

    def delete(self, key: str) -> dict:
        if self._use_memory:
            self._memory.pop(key, None)
            return {"result": 1}
        try:
            r = requests.post(
                self.url,
                json=["DEL", key],
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Redis Cache DEL Error (Key: {key}): {str(e)}")
            return {"result": 0}

    def keys(self, pattern: str):
        if self._use_memory:
            # Simple prefix match for memory mode
            prefix = pattern.rstrip("*")
            return [k for k in self._memory.keys() if k.startswith(prefix)]
        try:
            r = requests.post(
                self.url,
                json=["KEYS", pattern],
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()
            return r.json().get("result", [])
        except Exception as e:
            print(f"Redis Cache KEYS Error (Pattern: {pattern}): {str(e)}")
            return []


redis_cache = RedisCache()
