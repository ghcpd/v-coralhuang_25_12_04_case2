"""Advanced TODO backend package (initial implementation)

Exports get_backend() which returns a singleton backend instance when the
environment variable TODO_DB is set to a path; otherwise None.
"""
from .backend import get_backend  # re-export
__all__ = ["get_backend"]
