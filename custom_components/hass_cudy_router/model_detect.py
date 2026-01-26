from __future__ import annotations

import logging
import re
from typing import Any, Optional

_LOGGER = logging.getLogger(__name__)


# Known model mapping: pattern -> canonical model key used by models registry
KNOWN_MODELS = {
    r"WR6500": "WR6500",
    r"R700": "R700",
    r"WR-": "WR6500",  # fallback pattern
}


async def detect_model(client: Any) -> str:
    """Detect the router model using the provided transport client.

    The function attempts several endpoints that Cudy / LuCI-based firmwares
    commonly expose. It returns a canonical model key (for example
    "WR6500" or "R700"); if detection fails it returns a best-effort
    string (or a conservative default) and logs a warning.

    `client` is expected to implement an async `.get(path, **kwargs)` and
    expose `.stok` or `.auth_value` after authentication. This function
    will *not* attempt to mutate client state beyond calling `get()` which
    itself may authenticate.
    """

    # Try JSON-style system info endpoints first (some firmwares provide JSON)
    candidates = [
        "/api/system/info",
        "/cgi-bin/luci/;stok={stok}/admin/status/overview",
        "/cgi-bin/luci/;stok={stok}/admin/system/overview",
        "/cgi-bin/luci/;stok={stok}/admin/status/overview",
        "/cgi-bin/luci/;stok={stok}/admin/network/network",
    ]

    raw_text: Optional[str] = None

    # Attempt endpoints in order and stop on first usable response
    for path in candidates:
        try:
            # Insert stok if needed; client.get() will handle authentication if require_auth
            stok = getattr(client, "stok", None) or getattr(
                client, "auth_value", None
            ) or ""
            try_path = path.format(stok=stok)

            _LOGGER.debug("Trying model detect endpoint: %s", try_path)
            resp = await client.get(try_path)

            # Prefer dict-like JSON responses but accept text/html as fallback
            if isinstance(resp, dict):
                # Convert to string for regex-based scanning below
                raw_text = "\n".join(_flatten_dict_values(resp))
                break

            raw_text = str(resp)

            # break early if we got something non-empty
            if raw_text.strip():
                break

        except Exception as exc:  # pragma: no cover
            _LOGGER.debug("Model detect endpoint %s failed: %s", path, exc)
            continue

    if not raw_text:
        _LOGGER.warning(
            "Unable to fetch any system info for model detection; defaulting to WR6500"
        )
        return "WR6500"

    # Heuristics: look for known model tokens in text
    # Try to find explicit 'Model' or 'Hardware' fields first
    model = _first_match(
        raw_text,
        [
            r"Model\s*[:<]\s*([^\n<]+)",
            r"Hardware\s*[:<]\s*([^\n<]+)",
            r"model\W+([^\n<]+)",
        ],
    )

    if model:
        model = model.strip()
        _LOGGER.debug("Raw model string detected: %s", model)

        # Normalize using known mappings
        for pattern, canonical in KNOWN_MODELS.items():
            if re.search(pattern, model, re.IGNORECASE):
                _LOGGER.info(
                    "Detected router model: %s -> %s", model, canonical
                )
                return canonical

        # If no known pattern matched, return a cleaned token (no spaces)
        cleaned = re.sub(r"\s+", "", model)
        _LOGGER.info(
            "Detected unknown router model, returning cleaned token: %s",
            cleaned,
        )
        return cleaned

    # As a last resort, try to find model tokens directly in the body
    for pattern, canonical in KNOWN_MODELS.items():
        if re.search(pattern, raw_text, re.IGNORECASE):
            _LOGGER.info(
                "Detected router model by body token -> %s", canonical
            )
            return canonical

    _LOGGER.warning(
        "Model detection heuristics did not match any known models; defaulting to WR6500"
    )
    return "WR6500"


def _first_match(text: str, patterns: list[str]) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _flatten_dict_values(d: dict) -> list[str]:
    """Return a list of stringified values for a nested dict (breadth-first)."""
    out: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        else:
            out.append(str(x))

    walk(d)
    return out