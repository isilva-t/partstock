from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.olx import OLXAdvert, OLXDraftAdvert
from app.dependencies.olx import get_olx_service, get_olx_auth, OLXAdvertService
from app.models import Unit, Product
from app.integrations.olx.auth import OLXAuth
import httpx
from typing import List, Dict, Optional
from app.integrations.olx.constants import OLX
from app.dependencies.tools import get_tools

router = APIRouter()


@router.post("/send_all")
async def send_all_adverts(
    db: Session = Depends(get_db),
    olx_auth=Depends(get_olx_auth),
    service: OLXAdvertService = Depends(get_olx_service)
):
    """
    Placeholder: Send all draft adverts to OLX.
    """
    try:
        if not await olx_auth.is_token_bearer_valid():
            raise HTTPException(
                status_code=401, detail="OLX OAuth invalid or expired")

        drafts = db.query(OLXDraftAdvert).all()
        if not drafts:
            return {"message": "No draft adverts to send", }

        results = []
        successful = 0
        failed = 0

        for draft in drafts:
            result = await service.process_draft_to_olx(draft)
            results.append(result)
            if result.get("success"):
                successful += 1
            else:
                failed += 1

        return {
            "message": f"Sent {successful} adverts successfully, {failed} failed",
            "successful": successful,
            "failed": failed,
            "details": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send adverts: {str(e)}")


@router.get("/")
async def list_adverts(
    db: Session = Depends(get_db),
    olx_auth: OLXAuth = Depends(get_olx_auth),
    tools=Depends(get_tools),
):
    """
    List all OLX adverts with enriched data from OLX API.
    Automatically refreshes data from OLX when accessed.
    """

    try:
        # Get all local adverts
        local_adverts = db.query(OLXAdvert).all()

        # Fetch current data from OLX API
        olx_data = {}
        try:
            if await olx_auth.is_token_bearer_valid():
                olx_data = await _fetch_olx_adverts_data(olx_auth)
        except Exception as e:
            print(f"Warning: Failed to fetch OLX data: {e}")
        if not local_adverts:
            local_adverts = []

        enriched_adverts = []
        for advert in local_adverts:
            # Get unit and product data
            unit = db.query(Unit).filter(Unit.id == advert.unit_id).first()
            if not unit:
                continue

            product = db.query(Product).filter(
                Product.id == unit.product_id).first()
            if not product:
                continue

            # Get OLX data for this advert
            olx_info = olx_data.get(advert.olx_advert_id, {})

            enriched_adverts.append({
                "id": advert.id,
                "unit_id": advert.unit_id,
                "unit_reference": f"{product.sku}-{unit.sku}",
                "full_title": olx_info.get("title") or product.title,
                "selling_price": unit.selling_price,
                "olx_advert_id": advert.olx_advert_id,
                "olx_price": olx_info.get("price", "unavailable"),
                "status": (olx_info.get("status") or "")[:7],
                "valid_to": tools.format_dt(olx_info.get("valid_to")),
                "activated_at": tools.format_dt(olx_info.get("activated_at")),
                "created_at": tools.format_dt(olx_info.get("created_at")),
                "updated_at": tools.format_dt(olx_info.get("updated_at")),
                "olx_url": f"https://www.olx.pt/d/{advert.olx_advert_id}",
                # Additional data for actions
                "can_deactivate": olx_info.get("status") == "active",
                "can_finish": olx_info.get("status") == "limited"
            })

        if local_adverts:
            # Sort by status priority (active > limited > others)
            status_priority = {"active": 1, "limited": 2,
                               "removed_by_user": 3, "blocked": 4}
            enriched_adverts.sort(
                key=lambda x: status_priority.get(x["status"], 99))

            # Fetch DB adverts (only IDs)
            local_ids = {str(a.olx_advert_id)
                         for a in db.query(OLXAdvert).all()}
        else:
            local_ids = set()

        external_limited = []
        external = []
        for advert_id, olx_info in olx_data.items():
            if advert_id not in local_ids:

                status = olx_info.get("status")
                entry = {
                    "id": None,
                    "unit_id": None,
                    "unit_reference": None,
                    "full_title": olx_info.get("title"),
                    "selling_price": None,
                    "olx_advert_id": advert_id,
                    "olx_price": olx_info.get("price"),
                    "status": (status or "")[:7],
                    "valid_to": tools.format_dt(olx_info.get("valid_to")),
                    "created_at": tools.format_dt(olx_info.get("created_at")),
                    "updated_at": tools.format_dt(olx_info.get("updated_at")),
                    "olx_url": olx_info.get("url"),
                    "can_deactivate": False,
                    "can_finish": False
                }
                print("LETS 6 IT")
                if status == "limited":
                    external_limited.append(entry)
                elif status == "active":
                    external.append(entry)
                else:
                    # Show any other external adverts when we have no locals
                    if not local_adverts:
                        external.append(entry)

        external.extend(external_limited)

        return {
            "app_adverts": enriched_adverts,
            "external_adverts": external
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch adverts: {str(e)}")


@router.post("/{advert_id}/deactivate")
async def deactivate_advert(
    advert_id: int,
    db: Session = Depends(get_db),
    olx_auth: OLXAuth = Depends(get_olx_auth)
):
    """
    Deactivate an active OLX advert or finish a limited advert.
    """
    try:
        if not await olx_auth.is_token_bearer_valid():
            raise HTTPException(
                status_code=401, detail="OLX OAuth invalid or expired")

        # Get local advert
        advert = db.query(OLXAdvert).filter(OLXAdvert.id == advert_id).first()
        if not advert:
            raise HTTPException(status_code=404, detail="Advert not found")

        # Determine action based on current status
        if advert.status == "active":
            action = "deactivate"
            success_flag = True  # OLX requires is_success flag for deactivate
        elif advert.status == "limited":
            action = "finish"
            success_flag = None  # finish doesn't need is_success flag
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot {action} advert with status: {advert.status}")

        # Call OLX API
        result = await _send_advert_command(
            olx_auth, advert.olx_advert_id, action, success_flag)

        # Update local status
        new_status = "removed_by_user" if action == "deactivate" else "removed_by_user"
        advert.status = new_status
        db.commit()

        return {
            "message": f"Advert {action}d successfully",
            "action": action,
            "new_status": new_status,
            "olx_response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to {action} advert: {str(e)}")


# Helper functions

async def _fetch_olx_adverts_data(olx_auth: OLXAuth) -> Dict[str, Dict]:
    """
    Fetch all user's adverts from OLX API.
    Returns dict with olx_advert_id as key.
    """
    try:
        token = await olx_auth.get_user_token()
        if not token:
            return {}

        headers = {
            "Authorization": f"Bearer {token}",
            "Version": "2.0",
            "Accept": "application/json",
            "User-Agent": OLX.USER_AGENT,
        }

        result = {}
        offset = 0
        limit = 100

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await client.get(
                    f"https://www.olx.pt/api/partner/adverts?limit={
                        limit}&offset={offset}",
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()
                adverts_data = data.get("data", []) if isinstance(
                    data, dict) else data

                if not adverts_data:
                    break  # no more pages

                for advert in adverts_data:
                    advert_id = str(advert.get("id"))
                    result[advert_id] = {
                        "status": advert.get("status"),
                        "created_at": advert.get("created_at"),
                        "activated_at": advert.get("activated_at"),
                        "updated_at": advert.get("updated_at"),
                        "valid_to": advert.get("valid_to"),
                        "price": _extract_olx_price(advert.get("price", {})),
                        "title": advert.get("title"),
                        "url": advert.get("url"),
                    }

                offset += limit  # move to next page

        return result

    except Exception as e:
        print(f"Error fetching OLX adverts data: {e}")
        return {}


async def _send_advert_command(
    olx_auth: OLXAuth,
    olx_advert_id: str,
    command: str,
    is_success: Optional[bool] = None
) -> Dict:
    """
    Send command to OLX advert (deactivate, finish, etc.).
    """
    token = await olx_auth.get_user_token()
    if not token:
        raise Exception("No valid user token available")

    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": OLX.USER_AGENT,
    }

    payload = {"command": command}
    if is_success is not None:
        payload["is_success"] = is_success

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://www.olx.pt/api/partner/adverts/{olx_advert_id}/commands",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "success"}


def _extract_olx_price(price_data: Dict) -> str:
    """
    Extract readable price from OLX price object.
    """
    if not price_data:
        return "unavailable"

    value = price_data.get("value")

    if value is None:
        return "unavailable"

    return value
