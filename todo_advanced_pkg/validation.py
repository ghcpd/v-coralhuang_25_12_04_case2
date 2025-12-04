"""Validation utilities (placeholder).

Will be used to validate tag names, colors, and plugin schemas.
"""
import re

TAG_RE = re.compile(r"^[A-Za-z0-9_\-]{1,50}$")


def validate_tag_name(name: str) -> bool:
    return bool(TAG_RE.match(name))
