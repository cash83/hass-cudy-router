from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
import hashlib
import re
import time
from http.cookies import SimpleCookie
from urllib.parse import quote_plus

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


@dataclass
class CudyAuth:
    """Cookie-based LuCI auth."""
    sysauth: str


class CudyClient:
    """Low-level HTTP client for LuCI-based Cudy routers (cookie auth only)."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        use_https: bool = True,
        session: aiohttp.ClientSession | None = None,
        request_timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._use_https = use_https

        self._external_session = session is not None
        self._session: Optional[aiohttp.ClientSession] = session
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

        self._auth: Optional[CudyAuth] = None

    @property
    def base_url(self) -> str:
        scheme = "https" if self._use_https else "http"
        return f"{scheme}://{self._host}"

    @property
    def is_authenticated(self) -> bool:
        return self._auth is not None and bool(self._auth.sysauth)

    @property
    def sysauth(self) -> Optional[str]:
        return self._auth.sysauth if self._auth else None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed and not self._external_session:
            await self._session.close()

    async def authenticate(self) -> bool:
        session = await self._ensure_session()

        # Try preferred scheme first, then fallback (still LuCI-only).
        schemes = ["https", "http"] if self._use_https else ["http", "https"]

        def extract_input(html: str, name: str) -> str:
            m = re.search(
                rf"""<input\b[^>]*\bname\s*=\s*["']{re.escape(name)}["'][^>]*>""",
                html,
                flags=re.IGNORECASE,
            )
            if not m:
                return ""
            tag = m.group(0)
            mv = re.search(r"""value\s*=\s*["']([^"']*)["']""", tag, flags=re.IGNORECASE)
            return mv.group(1) if mv else ""

        def extract_meta(html: str, name: str) -> str:
            # e.g. <meta name="_csrf" content="...">
            m = re.search(
                rf"""<meta\b[^>]*\bname\s*=\s*["']{re.escape(name)}["'][^>]*>""",
                html,
                flags=re.IGNORECASE,
            )
            if not m:
                return ""
            tag = m.group(0)
            mv = re.search(r"""content\s*=\s*["']([^"']*)["']""", tag, flags=re.IGNORECASE)
            return mv.group(1) if mv else ""

        def best_effort_extract(html: str, key: str) -> str:
            return extract_input(html, key) or extract_meta(html, key)

        def compute_luci_password(password: str, salt: str, token: str) -> str:
            if not salt:
                return password
            hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            if token:
                hashed = hashlib.sha256((hashed + token).encode()).hexdigest()
            return hashed

        def parse_sysauth_from_headers(set_cookie_headers: list[str]) -> str | None:
            # Some firmwares use sysauth_http / sysauth_https
            for hdr in set_cookie_headers:
                cookie = SimpleCookie()
                cookie.load(hdr)
                for key in ("sysauth", "sysauth_http", "sysauth_https"):
                    morsel = cookie.get(key)
                    if morsel and morsel.value:
                        return morsel.value
            return None

        for scheme in schemes:
            base = f"{scheme}://{self._host}"
            login_url = f"{base}/cgi-bin/luci"

            headers_get = {
                "User-Agent": "Mozilla/5.0 (hass-cudy-router)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            headers_post = {
                "User-Agent": "Mozilla/5.0 (hass-cudy-router)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_url,
                "Origin": base,
            }

            # --- GET login page ---
            try:
                async with session.get(login_url, headers=headers_get, allow_redirects=True) as resp:
                    html = await resp.text()
                    status = resp.status
            except Exception as e:
                _LOGGER.error("GET login page failed (%s): %s", scheme, e)
                continue

            _csrf = best_effort_extract(html, "_csrf")
            token = best_effort_extract(html, "token")
            salt = best_effort_extract(html, "salt")

            # DEBUG: what did we extract?
            _LOGGER.debug(
                "LuCI login (%s) GET status=%s extracted: _csrf=%s token=%s salt=%s",
                scheme, status,
                "YES" if _csrf else "NO",
                "YES" if token else "NO",
                "YES" if salt else "NO",
            )

            zonename = "UTC"
            timeclock = str(int(time.time()))

            luci_password = compute_luci_password(self._password, salt, token)

            body = {
                "_csrf": _csrf,
                "token": token,
                "salt": salt,
                "zonename": zonename,
                "timeclock": timeclock,
                "luci_language": "en",
                "luci_username": self._username,
                "luci_password": luci_password,
                # sometimes needed by some skins (harmless if ignored)
                "submit": "1",
            }
            body = {k: v for k, v in body.items() if v}

            encoded = "&".join(f"{quote_plus(k)}={quote_plus(str(v))}" for k, v in body.items())

            # --- POST login ---
            try:
                async with session.post(login_url, headers=headers_post, data=encoded, allow_redirects=False) as resp:
                    post_status = resp.status
                    loc = resp.headers.get("Location", "")
                    set_cookies = resp.headers.getall("Set-Cookie", [])

                    # DEBUG: show what server does
                    _LOGGER.debug(
                        "LuCI login (%s) POST status=%s Location=%s Set-Cookie-count=%s",
                        scheme, post_status, loc, len(set_cookies)
                    )

                    sysauth = parse_sysauth_from_headers(set_cookies)
                    if sysauth:
                        self._auth = CudyAuth(sysauth=sysauth)
                        _LOGGER.debug("LuCI auth OK (%s): sysauth cookie set", scheme)
                        return True

                    # fallback: check cookie jar
                    jar = session.cookie_jar.filter_cookies(base)
                    for k in jar.keys():
                        if k.lower() in ("sysauth", "sysauth_http", "sysauth_https") and jar[k].value:
                            self._auth = CudyAuth(sysauth=jar[k].value)
                            _LOGGER.debug("LuCI auth OK (%s): sysauth from cookie jar (%s)", scheme, k)
                            return True

                    # If failing, log a tiny snippet of HTML (often contains “Access denied”)
                    try:
                        text = await resp.text()
                        _LOGGER.debug("LuCI login (%s) POST body head: %r", scheme, text[:200])
                    except Exception:
                        pass

            except Exception as e:
                _LOGGER.error("POST login failed (%s): %s", scheme, e)
                continue

        return False

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        require_auth: bool = True,
    ) -> Any:
        if not path.startswith("/"):
            path = "/" + path

        if require_auth and not self.is_authenticated:
            ok = await self.authenticate()
            if not ok:
                raise RuntimeError("Authentication failed (no sysauth cookie)")

        session = await self._ensure_session()
        url = f"{self.base_url}{path}"

        headers: dict[str, str] = {}
        if self.sysauth:
            headers["Cookie"] = f"sysauth={self.sysauth}"

        async def do() -> Any:
            async with session.request(method, url, params=params, json=json, data=data, headers=headers) as resp:
                if resp.status == 403 and require_auth:
                    # re-auth once and retry
                    ok2 = await self.authenticate()
                    if not ok2:
                        raise RuntimeError("Authentication failed after 403 retry")

                    headers2: dict[str, str] = {}
                    if self.sysauth:
                        headers2["Cookie"] = f"sysauth={self.sysauth}"

                    async with session.request(method, url, params=params, json=json, data=data, headers=headers2) as resp2:
                        resp2.raise_for_status()
                        ctype2 = resp2.headers.get("Content-Type", "")
                        if "application/json" in ctype2:
                            return await resp2.json(content_type=None)
                        return await resp2.text()

                resp.raise_for_status()
                ctype = resp.headers.get("Content-Type", "")
                if "application/json" in ctype:
                    return await resp.json(content_type=None)
                return await resp.text()

        return await do()

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    @classmethod
    def from_entry(cls, entry):
        data = entry.data
        protocol = (data.get("protocol") or "http").lower()
        return cls(
            host=data.get("host"),
            username=data.get("username"),
            password=data.get("password"),
            use_https=(protocol == "https"),
        )