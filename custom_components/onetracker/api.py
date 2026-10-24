"""Minimal async client for the public OneTracker API."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_BASE


class OneTrackerError(Exception):
    """Generic API or connection error."""


class OneTrackerAuthError(OneTrackerError):
    """Bad credentials, or a token that could not be refreshed."""


class OneTrackerClient:
    """Talks to https://api.onetracker.app (POST /auth/token, GET /parcels)."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._timeout = aiohttp.ClientTimeout(total=30)

    async def _login(self) -> None:
        try:
            async with self._session.post(
                f"{API_BASE}/auth/token",
                json={"email": self._email, "password": self._password},
                timeout=self._timeout,
            ) as resp:
                if resp.status in (400, 401, 403):
                    raise OneTrackerAuthError("Invalid email or password")
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise OneTrackerError(f"Cannot reach OneTracker: {err}") from err
        try:
            self._token = data["session"]["token"]
        except (KeyError, TypeError) as err:
            raise OneTrackerError("Unexpected login response") from err

    async def async_validate(self) -> None:
        """Log in once; raises on failure. Used by the config flow."""
        await self._login()

    async def async_get_parcels(self) -> list[dict[str, Any]]:
        """Return the parcel list, re-authenticating once if the token expired."""
        if self._token is None:
            await self._login()
        for attempt in (0, 1):
            try:
                async with self._session.get(
                    f"{API_BASE}/parcels",
                    headers={"x-api-token": self._token or ""},
                    timeout=self._timeout,
                ) as resp:
                    if resp.status == 401:
                        if attempt == 0:
                            await self._login()
                            continue
                        raise OneTrackerAuthError("Token rejected after re-login")
                    resp.raise_for_status()
                    data = await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise OneTrackerError(f"Cannot reach OneTracker: {err}") from err
            return data.get("parcels") or []
        return []
