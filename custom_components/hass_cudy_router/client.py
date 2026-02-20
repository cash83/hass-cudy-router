from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import re
from http.cookies import SimpleCookie
from typing import Any, Optional
from urllib.parse import quote_plus

import aiohttp
from aiohttp import ClientResponseError, ClientSession, TCPConnector
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


class CudyClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        use_https: bool = False,
        verify_ssl: bool = True,
        request_timeout: int = DEFAULT_TIMEOUT,
        session: ClientSession | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._use_https = use_https
        self._verify_ssl = verify_ssl

        self._external_session = session is not None
        self._session: Optional[ClientSession] = session
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

        self._sysauth: str | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def base_url(self) -> str:
        scheme = "https" if self._use_https else "http"
        return f"{scheme}://{self._host}"

    @property
    def is_authenticated(self) -> bool:
        return bool(self._sysauth)

    @property
    def sysauth(self) -> str | None:
        return self._sysauth

    # ------------------------------------------------------------------
    # Session handling
    # ------------------------------------------------------------------
    async def _ensure_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            connector = None
            # allow self-signed certs when verify_ssl=False
            if self._use_https and not self._verify_ssl:
                connector = TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(timeout=self._timeout, connector=connector)
        return self._session

    async def async_close(self) -> None:
        """Close the aiohttp session (called on HA unload)."""
        if self._session and not self._session.closed and not self._external_session:
            await self._session.close()
        self._session = None

    # backwards compat alias
    async def close(self) -> None:
        await self.async_close()

    # ------------------------------------------------------------------
    # Authentication (LuCI)
    # ------------------------------------------------------------------
    async def authenticate(self) -> bool:
        """Authenticate using the LuCI login form and set sysauth cookie."""

        session = await self._ensure_session()

        # try preferred scheme first, then fallback
        schemes = ["https", "http"] if self._use_https else ["http", "https"]

        for scheme in schemes:
            base = f"{scheme}://{self._host}"
            login_url = f"{base}/cgi-bin/luci"

            headers_get = {
                "User-Agent": "hass-cudy-router",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            headers_post = {
                "User-Agent": "hass-cudy-router",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_url,
                "Origin": base,
            }

            # 1) GET login page
            try:
                async with session.get(login_url, headers=headers_get, allow_redirects=True) as resp:
                    html = await resp.text()
            except Exception as e:
                _LOGGER.error("GET login page failed (%s): %s", scheme, e)
                continue

            if not html:
                _LOGGER.error("GET login page failed (%s): empty response", scheme)
                continue

            soup = BeautifulSoup(html, "html.parser")

            def extract(name: str) -> str:
                tag = soup.find("input", {"name": name})
                if tag and tag.has_attr("value"):
                    return str(tag["value"])
                # some firmwares put them in <meta>
                meta = soup.find("meta", {"name": name})
                if meta and meta.has_attr("content"):
                    return str(meta["content"])
                return ""

            _csrf = extract("_csrf")
            token = extract("token")
            salt = extract("salt")

            # 2) compute password
            luci_password = self._password
            if salt:
                hashed = hashlib.sha256((self._password + salt).encode()).hexdigest()
                if token:
                    hashed = hashlib.sha256((hashed + token).encode()).hexdigest()
                luci_password = hashed

            # 3) POST credentials
            body: dict[str, Any] = {
                "_csrf": _csrf,
                "token": token,
                "salt": salt,
                "zonename": "UTC",
                "timeclock": str(int(time.time())),
                "luci_language": "en",
                "luci_username": self._username,
                "luci_password": luci_password,
                "submit": "1",
            }
            body = {k: v for k, v in body.items() if v}

            encoded = "&".join(f"{quote_plus(k)}={quote_plus(str(v))}" for k, v in body.items())

            try:
                async with session.post(
                    login_url,
                    headers=headers_post,
                    data=encoded,
                    allow_redirects=False,
                ) as resp:
                    # try Set-Cookie header first
                    set_cookie = resp.headers.getall("Set-Cookie", [])
                    sysauth = self._parse_sysauth_from_headers(set_cookie)
                    if sysauth:
                        self._sysauth = sysauth
                        return True

                    # fallback to cookie jar
                    jar = session.cookie_jar.filter_cookies(base)
                    for key, cookie in jar.items():
                        if key.lower().startswith("sysauth") and cookie.value:
                            self._sysauth = cookie.value
                            return True
            except Exception as e:
                _LOGGER.error("POST login failed (%s): %s", scheme, e)
                continue

        _LOGGER.debug("Authentication failed: no sysauth cookie obtained")
        return False

    @staticmethod
    def _parse_sysauth_from_headers(set_cookie_headers: list[str]) -> str | None:
        for hdr in set_cookie_headers:
            cookie = SimpleCookie()
            cookie.load(hdr)
            for key in ("sysauth", "sysauth_http", "sysauth_https"):
                morsel = cookie.get(key)
                if morsel and morsel.value:
                    return morsel.value
        return None

    async def ensure_authenticated(self) -> None:
        if not self.is_authenticated:
            ok = await self.authenticate()
            if not ok:
                raise RuntimeError("Authentication failed")

    # ------------------------------------------------------------------
    # Generic request helpers
    # ------------------------------------------------------------------
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        require_auth: bool = True,
    ) -> Any:
        """Low-level request helper used by get/post and APIs."""

        if not path.startswith("/"):
            path = "/" + path

        if require_auth:
            await self.ensure_authenticated()

        session = await self._ensure_session()
        url = f"{self.base_url}{path}"

        headers: dict[str, str] = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
        }
        if self.sysauth:
            headers["Cookie"] = f"sysauth={self.sysauth}"

        async with session.request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
        ) as resp:
            if resp.status == 403 and require_auth:
                await self.authenticate()
                headers["Cookie"] = f"sysauth={self.sysauth}" if self.sysauth else ""
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                ) as resp2:
                    resp2.raise_for_status()
                    ctype = resp2.headers.get("Content-Type", "")
                    if "application/json" in ctype:
                        return await resp2.json(content_type=None)
                    return await resp2.text()

            try:
                resp.raise_for_status()
            except ClientResponseError:
                return ""

            ctype = resp.headers.get("Content-Type", "")
            if "application/json" in ctype:
                return await resp.json(content_type=None)
            return await resp.text()

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    async def get_json(self, path: str, **kwargs: Any) -> Any:
        """Explicit JSON helper if a caller wants JSON only."""
        return await self.request("GET", path, **kwargs)

    # ------------------------------------------------------------------
    # LuCI convenience helpers
    # ------------------------------------------------------------------
    async def luci_get(self, luci_path: str) -> str:
        """GET a LuCI path like '/admin/status/overview'."""
        if not luci_path.startswith("/"):
            luci_path = "/" + luci_path
        return await self.get(f"/cgi-bin/luci{luci_path}")

    async def luci_post(self, luci_path: str, data: dict[str, Any] | None = None) -> str:
        """POST to a LuCI path like '/admin/system/reboot'."""
        if not luci_path.startswith("/"):
            luci_path = "/" + luci_path
        return await self.post(f"/cgi-bin/luci{luci_path}", data=data)

    # ------------------------------------------------------------------
    # Cudy servicectl (runtime apply) helpers
    # ------------------------------------------------------------------
    _RE_TOKEN_JS = re.compile(r"token\s*:\s*'([0-9a-fA-F]{16,64})'")

    def _extract_token_anywhere(self, html: str) -> Optional[str]:
        """Try to extract the Cudy CSRF token from HTML/JS."""
        if not html:
            return None
        # 1) classic hidden input
        try:
            soup = BeautifulSoup(html, "html.parser")
            inp = soup.find("input", {"name": "token"})
            if inp and inp.has_attr("value"):
                t = str(inp["value"]).strip()
                if t:
                    return t
        except Exception:
            pass
        # 2) JS snippet: token: '...'
        m = self._RE_TOKEN_JS.search(html)
        if m:
            return m.group(1)
        return None

    async def _servicectl_restart(self, services: str, token: str, *, timeout_s: int = 35) -> bool:
        """Restart services via Cudy OEM endpoint and wait for finish."""
        await self.ensure_authenticated()
        session = await self._ensure_session()

        svc_url = f"{self.base_url}/cgi-bin/luci/admin/servicectl/restart/{services}"
        st_url = f"{self.base_url}/cgi-bin/luci/admin/servicectl/status"

        headers_post = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
            "Origin": self.base_url,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        headers_get = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
            "Origin": self.base_url,
        }
        if self.sysauth:
            headers_post["Cookie"] = f"sysauth={self.sysauth}"
            headers_get["Cookie"] = f"sysauth={self.sysauth}"

        # Start restart
        try:
            async with session.post(svc_url, data={"token": token}, headers=headers_post, allow_redirects=True) as r:
                _ = await r.text()
                if r.status >= 400:
                    _LOGGER.debug("servicectl restart %s failed status=%s", services, r.status)
                    return False
        except Exception as e:
            _LOGGER.debug("servicectl restart %s exception: %s", services, e)
            return False

        # Poll status until 'finish'
        deadline = time.time() + float(timeout_s)
        while time.time() < deadline:
            try:
                async with session.get(st_url, headers=headers_get, allow_redirects=True) as r2:
                    txt = (await r2.text()).strip().lower()
                    if txt == "finish":
                        return True
            except Exception:
                pass
            await asyncio.sleep(1)

        _LOGGER.debug("servicectl status timeout for %s", services)
        return False

    # ------------------------------------------------------------------
    # Wi-Fi control (Cudy custom UI / JSON endpoint)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Wi-Fi control (Cudy LuCI CBI form)
    # ------------------------------------------------------------------
    async def async_set_wifi(self, *args) -> bool:
        """
        Compat:
          - async_set_wifi(enabled)
          - async_set_wifi(band, enabled)   band: '2g'/'5g'/...

        Per gestire 2.4GHz e 5GHz separati (Smart Connect OFF) su Cudy:
          GET  /cgi-bin/luci/admin/network/wireless/config/uncombine?embedded=&nomodal=
          POST /cgi-bin/luci/admin/network/wireless/config/uncombine?embedded=&nomodal=
          multipart/form-data (aiohttp.FormData)

        IMPORTANTISSIMO:
          Il submit salva l'intera pagina -> bisogna inviare SEMPRE sia wlan00.disabled che wlan10.disabled
          preservando l'altra banda.
        """
        # --- parse args ---
        band = "2g"
        if len(args) == 1:
            enabled = bool(args[0])
        elif len(args) == 2:
            band = str(args[0]).lower()
            enabled = bool(args[1])
        else:
            raise TypeError("async_set_wifi expects (enabled) or (band, enabled)")

        if band in ("2.4g", "2g", "24g", "2_4g"):
            band = "2g"
        elif band in ("5g", "5ghz", "5"):
            band = "5g"
        else:
            # default safe
            band = "2g"

        await self.ensure_authenticated()
        session = await self._ensure_session()

        # 1) GET form vero (UNCOMBINE = Smart Connect OFF, con wlan00 + wlan10)
        ts = int(time.time() * 1000)
        get_url = f"{self.base_url}/cgi-bin/luci/admin/network/wireless/config/uncombine?embedded=&nomodal=&_={ts}"

        headers_get = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
        }
        if self.sysauth:
            headers_get["Cookie"] = f"sysauth={self.sysauth}"

        try:
            async with session.get(get_url, headers=headers_get, allow_redirects=True) as resp:
                status = resp.status
                html = await resp.text()
        except Exception as e:
            _LOGGER.error("Wi-Fi GET uncombine exception: %s", e)
            return False

        if status >= 400 or not html:
            _LOGGER.error("Wi-Fi GET uncombine failed status=%s", status)
            return False

        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", {"name": "cbi"}) or soup.find("form")
        if not form:
            _LOGGER.error("Wi-Fi form not found on uncombine head=%r", html[:200])
            return False

        # 2) Build payload completo (come browser)
        payload: dict[str, str] = {}

        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            itype = (inp.get("type") or "text").lower()

            if itype == "button":
                continue

            if itype in ("checkbox", "radio"):
                if inp.has_attr("checked"):
                    payload[name] = inp.get("value") or "1"
                continue

            payload[name] = inp.get("value") or ""

        for sel in form.find_all("select"):
            name = sel.get("name")
            if not name:
                continue
            opt = sel.find("option", selected=True) or sel.find("option")
            payload[name] = opt.get("value") if opt and opt.has_attr("value") else ""

        for ta in form.find_all("textarea"):
            name = ta.get("name")
            if not name:
                continue
            payload[name] = ta.text or ""

        token = payload.get("token", "")
        if not token:
            _LOGGER.error("Wi-Fi token missing in form payload")
            return False

        # 3) NON inviare campi 'combined' (Smart Connect) se presenti per sbaglio
        # (difesa extra: se li mandi, puoi riattivare Smart Connect)
        for k in list(payload.keys()):
            if k.startswith("cbid.wireless.wlan.") and not (
                k.startswith("cbid.wireless.wlan00.") or k.startswith("cbid.wireless.wlan10.")
            ):
                payload.pop(k, None)
            if k.startswith("cbi.cbe.wireless.wlan.") and not (
                k.startswith("cbi.cbe.wireless.wlan00.") or k.startswith("cbi.cbe.wireless.wlan10.")
            ):
                payload.pop(k, None)

        # 4) Preserva entrambi i flag e modifica solo quello richiesto
        # disabled: 0 = enabled, 1 = disabled
        disabled_val = "0" if enabled else "1"

        cur_2g = payload.get("cbid.wireless.wlan00.disabled", "0")
        cur_5g = payload.get("cbid.wireless.wlan10.disabled", "0")

        payload["cbi.cbe.wireless.wlan00.disabled"] = payload.get("cbi.cbe.wireless.wlan00.disabled", "1")
        payload["cbi.cbe.wireless.wlan10.disabled"] = payload.get("cbi.cbe.wireless.wlan10.disabled", "1")

        if band == "2g":
            payload["cbid.wireless.wlan00.disabled"] = disabled_val
            payload["cbid.wireless.wlan10.disabled"] = cur_5g
        else:  # "5g"
            payload["cbid.wireless.wlan10.disabled"] = disabled_val
            payload["cbid.wireless.wlan00.disabled"] = cur_2g

        # flags submit/apply (come browser)
        payload["cbi.submit"] = payload.get("cbi.submit", "1")
        payload["timeclock"] = payload.get("timeclock", str(int(time.time())))
        payload["cbi.apply"] = payload.get("cbi.apply", "1")

        # 5) POST allo stesso endpoint UNCOMBINE (multipart)
        post_url = f"{self.base_url}/cgi-bin/luci/admin/network/wireless/config/uncombine?embedded=&nomodal="

        headers_post = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
        }
        if self.sysauth:
            headers_post["Cookie"] = f"sysauth={self.sysauth}"

        formdata = aiohttp.FormData()
        for k, v in payload.items():
            formdata.add_field(k, str(v))

        try:
            async with session.post(post_url, headers=headers_post, data=formdata, allow_redirects=True) as resp2:
                body2 = await resp2.text()
                _LOGGER.debug(
                    "Wi-Fi POST uncombine band=%s enabled=%s -> wlan00=%s wlan10=%s status=%s head=%r",
                    band,
                    enabled,
                    payload.get("cbid.wireless.wlan00.disabled"),
                    payload.get("cbid.wireless.wlan10.disabled"),
                    resp2.status,
                    body2[:160],
                )
                if resp2.status >= 400:
                    return False

                # Apply runtime changes like the Cudy UI (restart wireless,vlan)
                tok = self._extract_token_anywhere(body2) or self._extract_token_anywhere(html) or token
                if tok:
                    ok_apply = await self._servicectl_restart('wireless,vlan', tok, timeout_s=35)
                    _LOGGER.debug('Wi-Fi servicectl apply wireless,vlan -> %s', ok_apply)
                else:
                    _LOGGER.debug('Wi-Fi servicectl token not found; skipping servicectl apply')
        except Exception as e:
            _LOGGER.error("Wi-Fi POST uncombine exception: %s", e)
            return False

        return True

    async def async_get_wifi_state(self) -> dict[str, bool]:
        """
        Legge lo stato reale dal router (Smart Connect OFF / uncombine):
          - 2.4G enabled se cbid.wireless.wlan00.disabled == "0"
          - 5G  enabled se cbid.wireless.wlan10.disabled == "0"
        Ritorna: {"2g": True/False, "5g": True/False}
        """
        await self.ensure_authenticated()
        session = await self._ensure_session()

        ts = int(time.time() * 1000)
        url = f"{self.base_url}/cgi-bin/luci/admin/network/wireless/config/uncombine?embedded=&nomodal=&_={ts}"

        headers_get = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
        }
        if self.sysauth:
            headers_get["Cookie"] = f"sysauth={self.sysauth}"

        async with session.get(url, headers=headers_get, allow_redirects=True) as resp:
            resp.raise_for_status()
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        def _val(name: str) -> str | None:
            inp = soup.find("input", {"name": name})
            if inp and inp.has_attr("value"):
                return str(inp["value"])
            return None

        v2 = _val("cbid.wireless.wlan00.disabled")
        v5 = _val("cbid.wireless.wlan10.disabled")

        # fallback safe: se non troviamo i campi, non inventiamo stati
        if v2 is None or v5 is None:
            raise RuntimeError("Wi-Fi status fields not found on uncombine page")

        return {
            "2g": (v2 == "0"),
            "5g": (v5 == "0"),
        }



# ------------------------------------------------------------------
# VPN control (WireGuard via LuCI CBI form)
# ------------------------------------------------------------------
    async def async_get_vpn_state(self) -> dict[str, bool]:
        """Ritorna lo stato VPN WireGuard (enabled/disabled).

        Firmware Cudy possono esporre il toggle su pagine diverse:
        - /admin/network/vpn/config?nomodal=
        - /admin/network/vpn (pagina principale)
        """
        await self.ensure_authenticated()
        session = await self._ensure_session()

        ts = int(time.time() * 1000)
        urls = [
            f"{self.base_url}/cgi-bin/luci/admin/network/vpn/config?nomodal=&_={ts}",
            f"{self.base_url}/cgi-bin/luci/admin/network/vpn?_={ts}",
        ]

        headers = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/network/vpn",
        }
        if self.sysauth:
            headers["Cookie"] = f"sysauth={self.sysauth}"

        last_err: Exception | None = None
        for url in urls:
            try:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    html = await resp.text()

                if not html:
                    raise RuntimeError(f"Empty VPN page: {url}")

                soup = BeautifulSoup(html, "html.parser")
                form = soup.find("form", {"name": "cbi"}) or soup.find("form")
                if not form:
                    # a volte torna una pagina di login o altro
                    raise RuntimeError("VPN form not found")

                # prova 1: match esatto
                inp = form.find("input", {"name": "cbid.vpn.config.enabled"})
                if inp and inp.has_attr("value"):
                    enabled_val = str(inp["value"]).strip()
                    return {"wireguard": (enabled_val == "1")}

                # prova 2: cerca un input che termina con '.enabled' e contiene 'vpn.config'
                enabled_val = None
                for el in form.find_all("input"):
                    name = (el.get("name") or "").strip()
                    if "vpn.config" in name and name.endswith(".enabled") and el.has_attr("value"):
                        enabled_val = str(el["value"]).strip()
                        break
                if enabled_val is not None:
                    return {"wireguard": (enabled_val == "1")}

                # prova 3: alcuni firmware usano checkbox checked (raro qui)
                cb = form.find("input", {"type": "checkbox"})
                if cb and (cb.get("name") or "").endswith("enabled"):
                    return {"wireguard": cb.has_attr("checked")}

                raise RuntimeError("VPN enabled field not found")
            except Exception as e:
                last_err = e
                continue

        raise RuntimeError(f"VPN state read failed: {last_err}")

    async def async_set_vpn(self, enabled: bool) -> bool:
        """Abilita/disabilita WireGuard Server (toggle Enable) preservando gli altri campi."""
        await self.ensure_authenticated()
        session = await self._ensure_session()
    
        ts = int(time.time() * 1000)
        get_url = f"{self.base_url}/cgi-bin/luci/admin/network/vpn/config?nomodal=&_={ts}"
    
        headers_get = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
        }
        if self.sysauth:
            headers_get["Cookie"] = f"sysauth={self.sysauth}"
    
        async with session.get(get_url, headers=headers_get, allow_redirects=True) as resp:
            html = await resp.text()
    
        if not html:
            _LOGGER.error("VPN GET config returned empty page")
            return False
    
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", {"name": "cbi"}) or soup.find("form")
        if not form:
            _LOGGER.error("VPN config form not found")
            return False
    
        # Estrai token (serve anche per restart firewall)
        token_val = None
        token_inp = form.find("input", {"name": "token"})
        if token_inp and token_inp.has_attr("value"):
            token_val = str(token_inp["value"]).strip()
    
        # timeclock (se c'è, aggiornalo)
        timeclock_val = None
        tc_inp = form.find("input", {"name": "timeclock"})
        if tc_inp and tc_inp.has_attr("value"):
            timeclock_val = str(int(time.time()))
    
        # Colleziona TUTTI i campi input/select/textarea
        fields: dict[str, str] = {}
        for el in form.find_all(["input", "select", "textarea"]):
            name = el.get("name")
            if not name:
                continue
            # skip buttons
            if el.name == "input" and el.get("type") in ("submit", "button", "image", "reset"):
                continue
            if el.name == "select":
                opt = el.find("option", selected=True) or el.find("option")
                if opt and opt.has_attr("value"):
                    fields[name] = str(opt["value"])
                continue
            if el.name == "textarea":
                fields[name] = el.text or ""
                continue
    
            # input
            typ = (el.get("type") or "").lower()
            if typ in ("checkbox", "radio"):
                # CBI spesso usa un hidden + checkbox; noi prendiamo value così com'è
                if el.has_attr("checked"):
                    fields[name] = str(el.get("value") or "1")
                else:
                    # se c'è già un valore dal hidden, non sovrascrivere
                    fields.setdefault(name, str(el.get("value") or "0"))
            else:
                if el.has_attr("value"):
                    fields[name] = str(el["value"])
    
        # Forza campi come da cattura browser
        fields["cbi.submit"] = fields.get("cbi.submit", "1")
        fields["cbi.apply"] = fields.get("cbi.apply", "1")
        fields["cbi.cbe.vpn.config.enabled"] = "1"
        fields["cbid.vpn.config.enabled"] = "1" if enabled else "0"
    
        if timeclock_val is not None:
            fields["timeclock"] = timeclock_val
    
        # POST multipart
        post_url = f"{self.base_url}/cgi-bin/luci/admin/network/vpn/config?nomodal="
        headers_post = {
            "User-Agent": "hass-cudy-router",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
            "Origin": self.base_url,
        }
        if self.sysauth:
            headers_post["Cookie"] = f"sysauth={self.sysauth}"
    
        formdata = aiohttp.FormData()
        for k, v in fields.items():
            formdata.add_field(k, v)
    
        try:
            async with session.post(post_url, data=formdata, headers=headers_post, allow_redirects=False) as resp:
                _ = await resp.text()
                loc = resp.headers.get("Location")
                if resp.status not in (200, 302, 303):
                    _LOGGER.error("VPN POST failed status=%s", resp.status)
                    return False
        except Exception as e:
            _LOGGER.error("VPN POST exception: %s", e)
            return False
    
        # segui location (optional) per coerenza con UI
        if loc:
            try:
                if not loc.startswith("http"):
                    loc_url = f"{self.base_url}{loc}"
                else:
                    loc_url = loc
                async with session.get(loc_url, headers=headers_get, allow_redirects=True) as _r:
                    await _r.text()
            except Exception:
                pass
    
        # Applica: restart firewall (come fa la UI)
        if token_val:
            try:
                svc_url = f"{self.base_url}/cgi-bin/luci/admin/servicectl/restart/firewall"
                data = {"token": token_val}
                headers_svc = {
                    "User-Agent": "hass-cudy-router",
                    "Accept": "*/*",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{self.base_url}/cgi-bin/luci/admin/setup",
                    "Origin": self.base_url,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }
                if self.sysauth:
                    headers_svc["Cookie"] = f"sysauth={self.sysauth}"
    
                async with session.post(svc_url, data=data, headers=headers_svc) as _r:
                    await _r.text()
            except Exception as e:
                _LOGGER.debug("VPN restart firewall failed: %s", e)
    
        return True

    # ------------------------------------------------------------------
    # Helper for tests / convenience
    # ------------------------------------------------------------------
    @classmethod
    def from_entry(cls, entry) -> "CudyClient":
        data = entry.data
        protocol = (data.get("protocol") or "http").lower()
        use_https = protocol == "https"
        return cls(
            host=data.get("host"),
            username=data.get("username"),
            password=data.get("password"),
            use_https=use_https,
        )
