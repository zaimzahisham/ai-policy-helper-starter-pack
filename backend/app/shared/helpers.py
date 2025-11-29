"""Shared helper functions."""
import uuid


def convert_to_uuid(hex_string: str) -> str:
    """
    Convert a hex string to UUID format (truncate/pad to 32 chars).
    
    UUIDs must be exactly 32 hex digits. This function handles both
    strings shorter than 32 chars (pads with zeros) and longer than
    32 chars (truncates).
    
    Args:
        hex_string: Hex string to convert (can be any length)
    
    Returns:
        UUID string in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    # Truncate/pad to 32 chars as UUIDs must be exactly 32 hex digits
    trimmed = hex_string[:32].ljust(32, "0")
    return str(uuid.UUID(trimmed))

