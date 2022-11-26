from re import sub


# List of acronyms that should be upper-cased instead of capitalized
_acronyms = (
    'rssi',  # Received Signal Strength Indicator
    'fw12',  # Firmware version 1.2 of Fleshlight Launch
)


def pascal_case(s: str) -> str:
    """Transforms strings from snake_case to PascalCase."""
    return ''.join(x.capitalize() if x not in _acronyms else x.upper() for x in s.split('_'))


def snake_case(s: str) -> str:
    """Transforms strings from PascalCase to snake_case."""
    return '_'.join(x.lower() for x in sub('([A-Z][a-z]+)', r' \1', sub('([A-Z]+)', r' \1', s)).split())
