import asyncio
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QListWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QApplication, QListWidgetItem,
)

from api import ApiClient
from config import VERSION
from ws_client import WebSocketWorker


class ChatWindow(QWidget):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.chat_id = None
        self.ws_worker = None

        self.setWindowTitle(f"NB Chat (alpha v-{VERSION})")
        self.resize(800, 600)

        layout = QHBoxLayout()

        # user list
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.load_user)
        layout.addWidget(self.user_list, 1)
        # Chats list
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_chat)
        layout.addWidget(self.chat_list, 1)

        # First part
        right = QVBoxLayout()

        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        right.addWidget(self.messages)

        self.msg_input = QLineEdit()
        self.msg_input.returnPressed.connect(self.send_message)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        send_layout = QHBoxLayout()
        send_layout.addWidget(self.msg_input)
        send_layout.addWidget(self.send_btn)

        right.addLayout(send_layout)

        layout.addLayout(right, 3)
        self.setLayout(layout)
        # if self.api.token:
        #     asyncio.create_task(self.load_chats())
        asyncio.create_task(self.load_users())
        # asyncio.create_task(self.start_ws_worker(self.chat_id))

    # def handle_global_event(self, msg: str):
    #     data = json.loads(msg)
    #     event_type = data.get("type")
    #
    #     if event_type == "message":
    #         chat_id = data["chat_id"]
    #         sender_id = data["sender_id"]
    #         content = data["content"]
    #
    #         # если это текущий чат — просто добавить сообщение
    #         if self.chat_id == chat_id:
    #             self.messages.append(f"{sender_id}: {content}")
    #         else:
    #             # можно сделать, чтобы выделялся новый чат, подсветка и т.д.
    #             print(f"📩 New message in chat {chat_id}")
    #
    #     elif event_type == "new_chat":
    #         asyncio.create_task(self.load_chats())
    #
    #
    # async def start_ws_worker(self, chat_id):
    #     # user = await self.api.get_current_user()
    #     if self.ws_worker:
    #         self.ws_worker.stop()
    #     self.ws_worker = WebSocketWorker(self.api.token, chat_id)
    #     self.ws_worker.event_received.connect(self.handle_global_event)
    #     self.ws_worker.start()

    def showEvent(self, event):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
        super().showEvent(event)

    async def load_users(self):
        self.chat_list.clear()
        users = await self.api.get_users()
        for user in users:
            item = QListWidgetItem(user["username"])
            item.setData(Qt.ItemDataRole.UserRole, user)
            self.user_list.addItem(item)

    async def _load_user_async(self, contact_user_id):
        chats = await self.api.get_chats()
        chat_id = None
        for chat in chats:
            if contact_user_id in chat.get("member_ids", []):
                chat_id = chat.get("chat_id")
                break
        if not chat_id:
            chat = await self.api.create_chat(member_ids=[contact_user_id], is_group=False)
            self.chat_id = chat["chat_id"]
            await self.load_chats()

    def load_user(self, item):
        contact_user_data = item.data(Qt.ItemDataRole.UserRole)
        contact_user_id = contact_user_data.get("id")
        asyncio.create_task(self._load_user_async(contact_user_id))

    async def load_chats(self):
        self.chat_list.clear()
        chats = await self.api.get_chats()
        for chat in chats:
            item = QListWidgetItem(f"Chat with {chat['chat_id']}")
            item.setData(Qt.ItemDataRole.UserRole, chat)
            self.chat_list.addItem(item)

    def load_chat(self, item):
        chat_data = item.data(Qt.ItemDataRole.UserRole)
        chat_id = chat_data.get("chat_id")
        self.chat_id = chat_id
        asyncio.create_task(self._load_messages(chat_id))

        if self.ws_worker:
            self.ws_worker.stop()
        self.ws_worker = WebSocketWorker(self.api.token, chat_id)
        self.ws_worker.message_received.connect(self.show_message)
        self.ws_worker.start()

    async def _load_messages(self, chat_id: int):
        self.messages.clear()
        msgs = await self.api.get_messages(chat_id)
        for m in msgs:
            self.messages.append(f"{m['sender_id']}: {m['content']}")

    def show_message(self, msg: str):
        data = json.loads(msg)
        self.messages.append(f"{data['sender_id']}: {data['content']}")

    async def _ensure_chat(self):
        """If there is no chat yet, we create a new automatically"""
        if not self.chat_id:
            chat = await self.api.create_chat(member_ids=[], is_group=False)
            self.chat_id = chat["chat_id"]
            await self.load_chats()

            if self.ws_worker:
                self.ws_worker.stop()
            self.ws_worker = WebSocketWorker(self.api.token, self.chat_id)
            self.ws_worker.message_received.connect(self.show_message)
            self.ws_worker.start()

    def send_message(self):
        text = self.msg_input.text()
        if not text.strip():
            return
        asyncio.create_task(self._send_message_flow(text))

    async def _send_message_flow(self, text: str):
        await self._ensure_chat()
        await self.api.send_message(self.chat_id, text)
        self.msg_input.clear()
        await self._load_messages(self.chat_id)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api = ApiClient()

        self.setWindowTitle("Login")
        layout = QVBoxLayout()

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        self.login_btn = QPushButton("Sign In")
        self.login_btn.clicked.connect(self.sign_in)
        layout.addWidget(self.login_btn)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.clicked.connect(self.sign_up)
        layout.addWidget(self.signup_btn)

        self.setLayout(layout)

        self.resize(400, 200)
        screen = self.screen()
        screen_center = screen.geometry().center()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_center)
        self.move(window_geometry.topLeft())

    def open_chat(self):
        self.chat = ChatWindow(self.api)
        self.chat.show()
        self.close()

    def sign_in(self):
        asyncio.create_task(self._sign_in())

    async def _sign_in(self):
        try:
            await self.api.sign_in(self.username.text(), self.password.text())
            self.open_chat()
            await self.chat.load_chats()
        except Exception as e:
            print("Login failed:", e)

    def sign_up(self):
        asyncio.create_task(self._sign_up())

    async def _sign_up(self):
        try:
            await self.api.sign_up(self.username.text(), self.password.text())
            self.open_chat()
        except Exception as e:
            print("Signup failed:", e)
