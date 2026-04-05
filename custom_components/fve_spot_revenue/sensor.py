"""Sensor platform for FVE SPOT Revenue CZ."""
from __future__ import annotations

import logging
import calendar
import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreSensor
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_EXPORT_SENSOR,
    CONF_PRICE_MODE,
    CONF_PRICE_SENSOR,
    CONF_FIXED_PRICE,
    CONF_FEE_PER_MWH,
    CONF_MONTHLY_FEE,
    PRICE_MODE_SPOT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    export_sensor_id = entry.data[CONF_EXPORT_SENSOR]
    price_mode = entry.data[CONF_PRICE_MODE]
    price_sensor_id = entry.data.get(CONF_PRICE_SENSOR)
    fixed_price = entry.data.get(CONF_FIXED_PRICE, 0.0)
    fee_per_mwh = entry.data.get(CONF_FEE_PER_MWH, 0.0)
    monthly_fee = entry.data.get(CONF_MONTHLY_FEE, 0.0)

    sensors = [
        FveRevenueSensor(
            hass, entry, export_sensor_id, price_mode, price_sensor_id, fixed_price, fee_per_mwh, monthly_fee, "daily", "Denní výnos FVE"
        ),
        FveRevenueSensor(
            hass, entry, export_sensor_id, price_mode, price_sensor_id, fixed_price, fee_per_mwh, monthly_fee, "weekly", "Týdenní výnos FVE"
        ),
        FveRevenueSensor(
            hass, entry, export_sensor_id, price_mode, price_sensor_id, fixed_price, fee_per_mwh, monthly_fee, "monthly", "Měsíční výnos FVE"
        ),
        FveRevenueSensor(
            hass, entry, export_sensor_id, price_mode, price_sensor_id, fixed_price, fee_per_mwh, monthly_fee, "yearly", "Roční výnos FVE"
        ),
    ]

    async_add_entities(sensors)


class FveRevenueSensor(RestoreSensor, SensorEntity):
    """Representation of a FVE Revenue Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "CZK"  # We assume CZK, could be configured

    def __init__(
        self, hass, entry, export_sensor_id, price_mode, price_sensor_id, 
        fixed_price, fee_per_mwh, monthly_fee, cycle, name
    ):
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry.entry_id
        self._export_sensor_id = export_sensor_id
        self._price_mode = price_mode
        self._price_sensor_id = price_sensor_id
        self._fixed_price = float(fixed_price) if fixed_price is not None else 0.0
        self._fee_per_mwh = float(fee_per_mwh) if fee_per_mwh is not None else 0.0
        self._monthly_fee = float(monthly_fee) if monthly_fee is not None else 0.0
        self._cycle = cycle
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{cycle}_revenue"
        self._state = 0.0

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self._state, 2)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        
        # Restore state
        state = await self.async_get_last_state()
        if state is not None:
            try:
                self._state = float(state.state)
            except ValueError:
                self._state = 0.0

        # Subscribe to export sensor changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._export_sensor_id], self._async_export_sensor_changed
            )
        )

        # Scheduled reset at midnight
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_midnight_hook, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_export_sensor_changed(self, event) -> None:
        """Handle export sensor state changes."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or old_state is None:
            return

        try:
            new_val = float(new_state.state)
            old_val = float(old_state.state)
        except ValueError:
            return

        delta_kwh = new_val - old_val

        # If sensor was reset (e.g., daily reset of the inverter), we ignore negative delta
        if delta_kwh <= 0:
            return

        # Get current price (assumed in CZK per kWh)
        current_price_kwh = self._fixed_price
        if self._price_mode == PRICE_MODE_SPOT and self._price_sensor_id:
            price_state = self.hass.states.get(self._price_sensor_id)
            if price_state is not None:
                try:
                    current_price_kwh = float(price_state.state)
                except ValueError:
                    _LOGGER.warning("Could not parse spot price: %s", price_state.state)
                    # If we can't parse price, we shouldn't calculate revenue for this delta
                    return

        # Fee is configured in MWh, convert into kWh margin
        fee_per_kwh = self._fee_per_mwh / 1000.0

        # Calculate revenue increment: Volume(kWh) * (Price(per kWh) - Fee(per kWh))
        revenue_inc = delta_kwh * (current_price_kwh - fee_per_kwh)
        self._state += revenue_inc
        self.async_write_ha_state()

    @callback
    def _async_midnight_hook(self, *_args) -> None:
        """Handle nightly reset and fee amortizations."""
        now = dt_util.now()
        
        # Calculate days in current month
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        daily_fee = self._monthly_fee / days_in_month

        should_reset = False

        if self._cycle == "daily":
            should_reset = True
        elif self._cycle == "weekly" and now.weekday() == 0:  # 0 is Monday
            should_reset = True
        elif self._cycle == "monthly" and now.day == 1:
            should_reset = True
        elif self._cycle == "yearly" and now.day == 1 and now.month == 1:
            should_reset = True

        if should_reset:
            # We reset the counter and apply the daily fee for the new period's first day
            self._state = -daily_fee
        else:
            # Not a reset day, we just subtract the daily amortized fee from the ongoing total
            self._state -= daily_fee

        self.async_write_ha_state()
