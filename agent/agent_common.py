"""
Stores content shared across agent classes + files.
"""


def try_getting(obj, *keys, default=None):
    """Helper that tries to get a value from a nested dict."""
    for key in keys:
        if key in obj:
            obj = obj[key]
        else:
            return default
    return obj