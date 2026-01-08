"""
String-compatible Enum base class.

This module defines `AutoStrEnum`, a convenience base class for enums whose
members behave like strings. It is useful for configuration values, protocol
identifiers, message types, and other enum-like constants that are frequently
compared to or serialized as plain strings.
"""

from enum import Enum


class AutoStrEnum(str, Enum):
    """
    String-compatible Enum base with natural string behavior.

    This enum base class:
      - Inherits from both `str` and `Enum`
      - Returns the underlying enum value when converted to a string
      - Allows direct comparison with string literals
      - Integrates cleanly with logging, JSON serialization, and f-strings

    Example:
        >>> class Status(AutoStrEnum):
        ...     OK = "ok"
        ...     ERROR = "error"
        >>>
        >>> Status.OK == "ok"
        True
        >>> f"status={Status.OK}"
        'status=ok'
    """

    def __str__(self) -> str:
        """
        Return the enum value as a string.

        This ensures that `str(enum_member)` yields the raw string value,
        rather than the default `Enum` representation.

        Returns:
            The enum's underlying string value.
        """
        return str(self.value)
