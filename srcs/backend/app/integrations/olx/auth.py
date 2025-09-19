import httpx
from datetime import datetime, timedelta
from app.config import settings
from sqlalchemy.orm import Session


class OLXAuth:
    def __init__(self, db: Session):

        self.access_token = settings.OLX_AUTH_BEARER  # MVP: static
        self.expires_at = None  # later: track expiry time

    async def is_token_bearer_valid(self) -> bool:
        if not self.access_token:
            return False
        return True
        #
        #
        # headers = {
        #     "Authorization": f"Bearer {self.access_token}",
        #     "Version": "2.0",
        #     "Accept": "application/json",
        # }
        # test_url = "https://www.olx.pt/api/partner/adverts?limit=1"
        #
        # try:
        #     async with httpx.AsyncClient(timeout=10) as client:
        #         resp = await client.get(test_url, headers=headers)
        #         return resp.status_code == 200
        # except Exception:
        #     return False

    def get_token(self) -> str:
        """Return token to be used in API calls."""
        return self.access_token
