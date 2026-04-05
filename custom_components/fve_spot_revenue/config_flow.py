"""Config flow for FVE SPOT Revenue CZ integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_EXPORT_SENSOR,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_FIXED_PRICE,
    CONF_FEE_PER_MWH,
    CONF_MONTHLY_FEE,
    PRICE_MODE_SPOT,
    PRICE_MODE_FIXED,
)

_LOGGER = logging.getLogger(__name__)

class FveSpotRevenueConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FVE SPOT Revenue CZ."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_PRICE_MODE] == PRICE_MODE_SPOT and not user_input.get(CONF_PRICE_SENSOR):
                errors["base"] = "missing_spot_sensor"
            elif user_input[CONF_PRICE_MODE] == PRICE_MODE_FIXED and user_input.get(CONF_FIXED_PRICE) is None:
                errors["base"] = "missing_fixed_price"
            else:
                title = f"Výnosy FVE: {user_input[CONF_EXPORT_SENSOR]}"
                return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_EXPORT_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(device_class="energy")
                ),
                vol.Required(CONF_PRICE_MODE, default=PRICE_MODE_SPOT): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[PRICE_MODE_SPOT, PRICE_MODE_FIXED],
                        translation_key="price_mode"
                    )
                ),
                vol.Optional(CONF_PRICE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Optional(CONF_FIXED_PRICE): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any"
                    )
                ),
                vol.Required(CONF_FEE_PER_MWH, default=0.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any"
                    )
                ),
                vol.Required(CONF_MONTHLY_FEE, default=0.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode=selector.NumberSelectorMode.BOX,
                        step="any"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
