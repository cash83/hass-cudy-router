from __future__ import annotations

from .coordinator import WR6500Coordinator
from ..base_button import async_setup_model_buttons, BUTTON_SPECS


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    await async_setup_model_buttons(
        hass,
        entry,
        async_add_entities,
        BUTTON_SPECS,
        coordinator_cls=WR6500Coordinator,
    )