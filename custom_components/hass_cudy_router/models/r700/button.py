from custom_components.hass_cudy_router.models.base_button import BUTTON_SPECS, async_setup_model_buttons
from custom_components.hass_cudy_router.models.r700 import R700Coordinator


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    await async_setup_model_buttons(
        hass,
        entry,
        async_add_entities,
        BUTTON_SPECS,
        coordinator_cls=R700Coordinator,
    )