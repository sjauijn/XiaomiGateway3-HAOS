import asyncio

from .shell_e1 import ShellE1
from .shell_mgw import ShellMGW
from .shell_mgw2 import ShellMGW2


class Session:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(
        self,
        host: str,
        port=23,
        telnet_login: str = None,
        telnet_password: str = None,
    ):
        self.coro = asyncio.open_connection(host, port, limit=1_000_000)
        self.telnet_login = telnet_login
        self.telnet_password = telnet_password

    async def __aenter__(self):
        await self.connect()
        try:
            return await self.login()
        except BaseException:
            try:
                await self.close()
            except Exception:
                pass
            raise

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        self.reader, self.writer = await asyncio.wait_for(self.coro, 5)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def login(self) -> ShellMGW | ShellE1 | ShellMGW2:
        coro = self.reader.readuntil(b"login: ")
        resp: bytes = await asyncio.wait_for(coro, 3)

        if b"rlxlinux" in resp:
            shell = ShellMGW(self.reader, self.writer, self.telnet_login, self.telnet_password)
        elif b"Aqara-Hub-E1" in resp or b"Aqara_Hub_E1" in resp:
            shell = ShellE1(self.reader, self.writer, self.telnet_login, self.telnet_password)
        elif b"Mijia_Hub_V2" in resp:
            shell = ShellMGW2(self.reader, self.writer, self.telnet_login, self.telnet_password)
        else:
            raise Exception(f"Unknown response: {resp}")

        await shell.login()
        await shell.prepare()

        return shell
