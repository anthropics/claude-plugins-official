"""KVKK provider seam; live decision and guidance integration is unwired."""
from .base import BaseLegalSourceProvider


class KVKKProvider(BaseLegalSourceProvider):
    source_id = "kvkk"
    source_name = "Kişisel Verileri Koruma Kurumu"
    source_type = "regulator"

