from __future__ import annotations

from typing import Any

from aiohttp import ClientResponseError

from .client import CudyClient
from .const import *
from .parser import parse_html


class CudyApi:
    def __init__(self, client: CudyClient) -> None:
        self._client = client

    @staticmethod
    def luci(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return "/cgi-bin/luci" + path

    async def get_data(self) -> dict[str, Any]:
        out: dict[str, Any] = {}

        for module in CAPABILITY_URLS.keys():
            url = CAPABILITY_URLS[module][0]
            try:
                html = await self._client.get(self.luci(url))
                if html is not None:
                    data = parse_html(module, html)
                    if len(data) > 0:
                        out[module] = data
            except ClientResponseError as err:
                """No module detected"""
        return out

    async def reboot(self) -> None:
        await self._client.post(self.luci("/admin/system/reboot"), data={"reboot": "1"})