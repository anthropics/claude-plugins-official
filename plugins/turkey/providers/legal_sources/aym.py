"""AYM provider seam; live karar arama integration is unwired."""
from .base import BaseLegalSourceProvider


class AYMProvider(BaseLegalSourceProvider):
    source_id = "aym"
    source_name = "Anayasa Mahkemesi"
    source_type = "court"

