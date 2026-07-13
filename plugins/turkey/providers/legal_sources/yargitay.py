"""Yargıtay provider seam; live karar arama integration is unwired."""
from .base import BaseLegalSourceProvider


class YargitayProvider(BaseLegalSourceProvider):
    source_id = "yargitay"
    source_name = "Yargıtay"
    source_type = "court"

