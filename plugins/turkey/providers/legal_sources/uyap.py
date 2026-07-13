"""UYAP provider seam; live UYAP integration is intentionally unwired."""
from .base import BaseLegalSourceProvider


class UYAPProvider(BaseLegalSourceProvider):
    source_id = "uyap"
    source_name = "UYAP"
    source_type = "court"

