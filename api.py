import httpx

from config import API_URL


class ApiClient:
    def __init__(self):
        self.token = None
        self.client = httpx.AsyncClient(follow_redirects=True)

    async def sign_in(self, username: str, password: str):
        resp = await self.client.post(f"{API_URL}/auth/sign-in/", json={
            "username": username,
            "password": password
        })
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    async def sign_up(self, username: str, password: str):
        resp = await self.client.post(f"{API_URL}/auth/sign-up/", json={
            "username": username,
            "password": password
        })
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    async def get_users(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{API_URL}/users/full-list", headers=headers)
        resp.raise_for_status()
        return resp.json()

    # async def get_current_user(self):
    #     headers = {"Authorization": f"Bearer {self.token}"}
    #     resp = await self.client.get(f"{API_URL}/users/current-user", headers=headers)
    #     resp.raise_for_status()
    #     return resp.json()

    async def get_chats(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{API_URL}/chats/", headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def get_messages(self, chat_id: int):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{API_URL}/chats/{chat_id}/messages/", headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def send_message(self, chat_id: int, content: str):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.post(
            f"{API_URL}/chats/{chat_id}/messages/",
            headers=headers,
            json={"content": content}
        )
        resp.raise_for_status()
        return resp.json()

    async def create_chat(self, member_ids: list[int], is_group: bool = False):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.post(
            f"{API_URL}/chats/",
            headers=headers,
            json={"member_ids": member_ids, "is_group": is_group}
        )
        resp.raise_for_status()
        return resp.json()
