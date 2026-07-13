"""Danıştay provider seam; live karar arama integration is unwired."""
from .base import BaseLegalSourceProvider


class DanistayProvider(BaseLegalSourceProvider):
    source_id = "danistay"
    source_name = "Danıştay"
    source_type = "court"

