from typing import Any, Callable


def apply_to_keys(d: dict[str, Any], f: Callable[[str], str]) -> dict[str, Any]:
    """Applies the provided function `f` to all keys in a dict."""
    return {f(key): value for key, value in d.items()}
