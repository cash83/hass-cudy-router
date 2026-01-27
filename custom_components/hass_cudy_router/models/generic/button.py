from custom_components.hass_cudy_router.models.base_button import async_setup_model_buttons, BUTTON_SPECS
from custom_components.hass_cudy_router.models.generic import GenericCoordinator


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    await async_setup_model_buttons(
        hass,
        entry,
        async_add_entities,
        BUTTON_SPECS,
        coordinator_cls=GenericCoordinator,
    )