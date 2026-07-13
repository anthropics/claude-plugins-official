"""Mevzuat Bilgi Sistemi provider seam; live integration is unwired."""
from .base import BaseLegalSourceProvider


class MevzuatBilgiSistemiProvider(BaseLegalSourceProvider):
    source_id = "mevzuat-bilgi-sistemi"
    source_name = "Mevzuat Bilgi Sistemi"
    source_type = "legislature"

