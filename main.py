import asyncio
import sys

import qasync
from PyQt6.QtWidgets import QApplication

from ui import LoginWindow


def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    login = LoginWindow()
    login.show()
    with loop:
        loop.run_forever()
    # sys.exit(app.exec())


if __name__ == "__main__":
    import platform
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # for Windows
    main()
