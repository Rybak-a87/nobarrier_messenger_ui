import asyncio
import json

import websockets
from PyQt6.QtCore import QThread, pyqtSignal

from config import WS_URL


class WebSocketWorker(QThread):
    message_received = pyqtSignal(str)
    new_chat = pyqtSignal(dict)
    event_received = pyqtSignal(str)

    def __init__(self, token: str, chat_id: int):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.running = True

    async def ws_loop(self):
        uri = f"{WS_URL}/{self.chat_id}?token={self.token}"
        async with websockets.connect(uri) as ws:
            while self.running:
                message = await ws.recv()
                self.message_received.emit(message)
                # data = json.loads(message)
                # if data["type"] == "message":
                #     self.message_received.emit(data)
                # elif data["type"] == "new_chat":
                #     self.new_chat.emit(data)
                # self.event_received.emit(message)

    def run(self):
        asyncio.run(self.ws_loop())

    def stop(self):
        self.running = False
        self.quit()
