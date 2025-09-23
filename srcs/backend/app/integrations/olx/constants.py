from decimal import Decimal
import math
from app.config import settings


class OLX:
    OAUTH_URL = "https://www.olx.pt/api/partner/oauth/token"
    ADVERTS_URL = "https://www.olx.pt/api/partner/adverts"

    CATEGORY_ID = 377  # pecas e acessorios
    ADVERTISER_TYPE = "business"
    CONTACT_NAME = settings.OLX_CONTACT_NAME
    CONTACT_PHONE = settings.OLX_CONTACT_PHONE
    CITY_ID = 1063945  # ovar
    CURRENCY = "EUR"

    VAT_MULTIPLIER = Decimal("1.23")  # could move to .env

    @classmethod
    def calc_price(cls, selling_price: int) -> int:
        euro_price = Decimal(selling_price) / 100
        with_vat = euro_price * cls.VAT_MULTIPLIER
        return math.ceil(with_vat)

    ATTRIBUTES = [{"code": "state", "value": "used"}]

    STATUS_LIMITED = "limited"
    STATUS_ACTIVE = "active"
    STATUS_REMOVED = "removed_by_user"
    STATUS_PENDING = "pending"
    STATUS_BLOCKED = "blocked"

    AUTH_URL = "https://www.olx.pt/oauth/authorize"
    TOKEN_URL = "https://www.olx.pt/api/open/oauth/token"
    USER_AGENT = "PartStock/1.0"

    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
