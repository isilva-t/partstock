from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.olx import get_olx_auth
from app.integrations.olx.auth import OLXAuth
from app.model.olx import OLXToken
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/auth/start")
async def start_oauth_flow(
    request: Request,
    olx_auth: OLXAuth = Depends(get_olx_auth)
):
    """
    Start OAuth authorization flow.
    Redirects user to OLX for manual authorization.
    """
    try:
        # Generate OAuth URL with callback
        callback_url = "http://autobock.duckdns.org:8080/api/v1/olx/auth/callback"
        oauth_url = olx_auth.get_oauth_url(redirect_uri=callback_url)

        # Redirect user to OLX
        return RedirectResponse(url=oauth_url, status_code=302)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )


@router.get("/auth/callback")
async def oauth_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    olx_auth: OLXAuth = Depends(get_olx_auth)
):
    """
    Handle OAuth callback from OLX.
    Exchanges authorization code for access tokens.
    """
    # Check for OAuth errors
    if error:
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": f"OAuth authorization failed: {error}",
            "token_status": None
        })

    # Validate required parameters
    if not code:
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": "Missing authorization code from OLX",
            "token_status": None
        })

    if state != "partstock_auth":
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": "Invalid state parameter - possible security issue",
            "token_status": None
        })

    try:
        # Exchange code for tokens
        callback_url = str(request.base_url).rstrip(
            '/') + "/api/v1/olx/auth/callback"
        success = await olx_auth.handle_oauth_callback(code, redirect_uri=callback_url)

        if success:
            return templates.TemplateResponse("olx_auth_status.html", {
                "request": request,
                "success": "Successfully connected to OLX! You can now create adverts.",
                "token_status": _get_token_status(olx_auth)
            })
        else:
            return templates.TemplateResponse("olx_auth_status.html", {
                "request": request,
                "error": "Failed to exchange authorization code for tokens",
                "token_status": None
            })

    except Exception as e:
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": f"OAuth callback failed: {str(e)}",
            "token_status": None
        })


@router.get("/auth/status", response_class=HTMLResponse)
async def auth_status_page(
    request: Request,
    olx_auth=Depends(get_olx_auth)
):
    """
    Admin page showing OLX authentication status.
    """
    try:

        try:
            await olx_auth.get_client_token()
        except Exception as e:
            print(f"Client token acquisition failed: {e}")

        token_status = _get_token_status(olx_auth)

        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "token_status": token_status,
            "oauth_start_url": "/api/v1/olx/auth/start"
        })

    except Exception as e:
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": f"Failed to check authentication status: {str(e)}",
            "token_status": None
        })


@router.post("/auth/disconnect")
async def disconnect_olx(
    request: Request,
    olx_auth: OLXAuth = Depends(get_olx_auth),
    db: Session = Depends(get_db)
):
    """
    Disconnect from OLX by removing user token.
    """
    try:
        # Delete user token from database
        olx_auth._delete_token("user")

        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "success": "Disconnected from OLX successfully.",
            "token_status": _get_token_status(olx_auth)
        })

    except Exception as e:
        return templates.TemplateResponse("olx_auth_status.html", {
            "request": request,
            "error": f"Failed to disconnect: {str(e)}",
            "token_status": _get_token_status(olx_auth)
        })


# ===== API ENDPOINTS FOR AJAX =====

@router.get("/auth/check")
async def check_auth_status(
    olx_auth: OLXAuth = Depends(get_olx_auth)
):
    """
    API endpoint to check authentication status.
    Used by frontend for dynamic feature enabling.
    """
    try:
        return {
            "user_authorized": olx_auth.is_user_authorized(),
            "token_status": _get_token_status(olx_auth)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check auth status: {str(e)}"
        )


# ===== HELPER FUNCTIONS =====

def _get_token_status(olx_auth: OLXAuth) -> dict:
    """
    Get comprehensive token status information.
    """
    try:
        db = olx_auth.db

        # Get tokens from database
        client_token = db.query(OLXToken).filter(
            OLXToken.token_type == "client").first()
        user_token = db.query(OLXToken).filter(
            OLXToken.token_type == "user").first()

        status = {
            "client_token": {
                "exists": client_token is not None,
                "valid": client_token and olx_auth._is_token_valid(client_token),
                "expires_at": client_token.expires_at.strftime('%Y-%m-%d %H:%M') if client_token else None,
                "scope": client_token.scope if client_token else None
            },
            "user_token": {
                "exists": user_token is not None,
                "valid": user_token and olx_auth._is_token_valid(user_token),
                "expires_at": user_token.expires_at.strftime('%Y-%m-%d %H:%M') if user_token else None,
                "scope": user_token.scope if user_token else None,
                "has_refresh": user_token and user_token.refresh_token is not None
            }
        }

        return status

    except Exception as e:
        return {
            "error": f"Failed to get token status: {str(e)}",
            "client_token": {"exists": False, "valid": False},
            "user_token": {"exists": False, "valid": False}
        }
