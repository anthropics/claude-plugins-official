"""Resmî Gazete provider seam; live archive integration is unwired."""
from .base import BaseLegalSourceProvider


class ResmiGazeteProvider(BaseLegalSourceProvider):
    source_id = "resmi-gazete"
    source_name = "Resmî Gazete"
    source_type = "official_gazette"

