import httpx
from datetime import datetime, timedelta
from app.config import settings
from sqlalchemy.orm import Session
from typing import Optional
from app.model.olx import OLXToken
from app.integrations.olx.constants import OLX


class OLXAuth:
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.OLX_CLIENT_ID
        self.client_secret = settings.OLX_CLIENT_SECRET
        self.access_token = settings.OLX_AUTH_BEARER  # MVP: static
        self.expires_at = None  # later: track expiry time

    async def get_client_token(self) -> str:
        """
        Get client_credentials token for config operations.
        Automatically acquires/refreshes as needed.
        """
        token = self._get_token_from_db("client")

        if token and self._is_token_valid(token):
            return token.access_token

        # Need new client token
        return await self._acquire_client_token()

    async def get_user_token(self) -> Optional[str]:
        """
        Get user token for advert operations.
        Returns None if no valid user authorization exists.
        """
        token = self._get_token_from_db("user")

        if not token:
            return None

        if self._is_token_valid(token):
            return token.access_token

        # Try to refresh user token
        if token.refresh_token:
            try:
                await self._refresh_user_token(token)
                return token.access_token
            except Exception:
                # Refresh failed, user needs to re-authorize
                self._delete_token("user")
                return None

        return None

    # ===== OAUTH FLOW METHODS =====

    def get_oauth_url(self, redirect_uri: str = None) -> str:
        """
        Generate OAuth authorization URL for manual user setup.
        """
        redirect_uri = redirect_uri or settings.OLX_OAUTH_CALLBACK

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "read write v2",
            "redirect_uri": redirect_uri,
            "state": "partstock_auth"  # Simple state for verification
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{OLX.AUTH_URL}?{query_string}"

    async def handle_oauth_callback(self, code: str,
                                    redirect_uri: str = None) -> bool:
        """
        Process OAuth callback and store user token.
        Returns True on success, False on failure.
        """
        redirect_uri = redirect_uri or settings.OLX_OAUTH_CALLBACK

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "scope": "read write v2",
            "redirect_uri": redirect_uri
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(OLX.TOKEN_URL,
                                             json=payload,
                                             headers=OLX.DEFAULT_HEADERS)
                response.raise_for_status()

                data = response.json()

                # Store user token in database
                self._store_token(
                    token_type="user",
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_in=data["expires_in"],
                    scope=data.get("scope", "v2 read write")
                )

                return True

        except Exception as e:
            print(f"OAuth callback failed: {e}")
            return False

    def is_user_authorized(self) -> bool:
        """
        Quick check if user token exists and is valid.
        Used by frontend to show/hide features.
        """
        token = self._get_token_from_db("user")
        return token is not None and self._is_token_valid(token)

    async def is_token_bearer_valid(self) -> bool:
        """
        Legacy method compatibility - checks if user token is available.
        """
        return self.is_user_authorized()

    def get_token(self) -> str:
        """
        Legacy method compatibility - returns user token if available.
        Raises exception if no user token (for advert operations).
        """
        token = self._get_token_from_db("user")
        if not token or not self._is_token_valid(token):
            raise Exception(
                "No valid user token available. Please authorize first.")
        return token.access_token

    # ===== PRIVATE HELPER METHODS =====

    async def _acquire_client_token(self) -> str:
        """
        Acquire new client_credentials token.
        """
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "v2 read"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLX.TOKEN_URL,
                                         json=payload,
                                         headers=OLX.DEFAULT_HEADERS)
            response.raise_for_status()

            data = response.json()

            # Store client token (no refresh_token)
            self._store_token(
                token_type="client",
                access_token=data["access_token"],
                refresh_token=None,
                expires_in=data["expires_in"],
                scope=data.get("scope", "v2 read")
            )

            return data["access_token"]

    async def _refresh_user_token(self, token: OLXToken) -> None:
        """
        Refresh user token using refresh_token.
        """
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": token.refresh_token
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLX.TOKEN_URL,
                                         json=payload,
                                         headers=OLX.DEFAULT_HEADERS)
            response.raise_for_status()

            data = response.json()

            # Update existing token
            token.access_token = data["access_token"]
            token.refresh_token = data.get(
                "refresh_token", token.refresh_token)
            token.expires_at = datetime.utcnow(
            ) + timedelta(seconds=data["expires_in"])
            token.updated_at = datetime.utcnow()

            self.db.commit()

    def _get_token_from_db(self, token_type: str) -> Optional[OLXToken]:
        """
        Retrieve token from database by type.
        """
        return self.db.query(OLXToken).filter(
            OLXToken.token_type == token_type
        ).first()

    def _store_token(self, token_type: str,
                     access_token: str,
                     refresh_token: Optional[str],
                     expires_in: int, scope: str) -> None:
        """
        Store or update token in database.
        """
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Check if token already exists
        existing = self._get_token_from_db(token_type)

        if existing:
            # Update existing
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.expires_at = expires_at
            existing.scope = scope
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            new_token = OLXToken(
                token_type=token_type,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                scope=scope
            )
            self.db.add(new_token)

        self.db.commit()

    def _is_token_valid(self, token: OLXToken) -> bool:
        """
        Check if token is still valid (not expired).
        Uses 5-minute buffer for safety.
        """
        if not token:
            return False

        buffer = timedelta(minutes=5)
        return datetime.utcnow() < (token.expires_at - buffer)

    def _delete_token(self, token_type: str) -> None:
        """
        Delete token from database.
        """
        token = self._get_token_from_db(token_type)
        if token:
            self.db.delete(token)
            self.db.commit()
