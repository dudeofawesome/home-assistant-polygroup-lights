"""Constants for the TOTO Washlet integration."""

DOMAIN = "toto_washlet"
CONF_INFRARED_ENTITY_ID = "infrared_entity_id"
CONF_INFRARED_RECEIVER_ENTITY_ID = "infrared_receiver_entity_id"


def received_command_signal(entry_id: str) -> str:
    """Return the dispatcher signal for received Washlet commands."""
    return f"{DOMAIN}_{entry_id}_received_command"
