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

        for module, urls in CAPABILITY_URLS.items():
            if not urls:
                continue

            module_data: dict[str, Any] | list[Any] | None = None

            # Try multiple known URLs (firmware-dependent)
            for url in urls:
                try:
                    html = await self._client.get(self.luci(url))
                except ClientResponseError:
                    continue

                if not html:
                    continue

                data = parse_html(module, html)

                # Handle XHR "shell" pages: fetch real fragments and merge
                if isinstance(data, dict) and "xhr_endpoints" in data:
                    merged: dict[str, Any] = {}
                    xhr = data.get("xhr_endpoints") or {}
                    if isinstance(xhr, dict):
                        for ep, meta in xhr.items():
                            try:
                                args = ""
                                if isinstance(meta, dict):
                                    args = meta.get("args", "") or ""
                                path = ep
                                if args:
                                    # args is already a querystring
                                    sep = "&" if "?" in path else "?"
                                    path = f"{path}{sep}{args}"
                                frag = await self._client.get(path)
                                if not frag:
                                    continue
                                frag_data = parse_html(module, frag)
                                if isinstance(frag_data, dict):
                                    merged.update(frag_data)
                            except ClientResponseError:
                                continue
                            except Exception:
                                continue
                    data = merged

                # Accept non-empty dicts and non-empty lists
                if isinstance(data, dict) and len(data) > 0:
                    module_data = data
                    break
                if isinstance(data, list) and len(data) > 0:
                    module_data = data
                    break

            if module_data is not None:
                out[module] = module_data

        # --- Heuristic enrichment for Cudy P4 5G/LTE firmwares -----------------
        # Some firmwares don't expose a classic WAN status page; the useful info
        # lives under GSM/4G (gcom). Map what we can so HA doesn't show
        # "Sconosciuto" everywhere.
        try:
            gsm = out.get(MODULE_GSM)
            wan = out.get(MODULE_WAN)

            if isinstance(gsm, dict):
                if not isinstance(wan, dict):
                    wan = {}
                    out[MODULE_WAN] = wan

                # Prefer explicit WAN values, otherwise derive from GSM.
                wan.setdefault(SENSOR_WAN_PUBLIC_IP, gsm.get(SENSOR_GSM_PUBLIC_IP) or gsm.get(SENSOR_GSM_IP_ADDRESS))
                wan.setdefault(SENSOR_WAN_IP, gsm.get(SENSOR_GSM_IP_ADDRESS) or gsm.get(SENSOR_GSM_PUBLIC_IP))
                wan.setdefault(SENSOR_WAN_TYPE, gsm.get(SENSOR_GSM_NETWORK_TYPE))
                wan.setdefault(SENSOR_WAN_UPTIME, gsm.get(SENSOR_GSM_CONNECTED_TIME))
        except Exception:
            pass

        return out

    async def reboot(self) -> None:
        await self._client.post(self.luci("/admin/system/reboot"), data={"reboot": "1"})