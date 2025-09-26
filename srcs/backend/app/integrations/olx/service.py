import httpx
from app.models import Unit, Product, ProductCompatibility, Model
from app.integrations.olx.constants import OLX
from sqlalchemy.orm import Session
from app.integrations.olx.auth import OLXAuth
from app.models import UnitPhoto
from app.config import settings
from app.model.olx import OLXDraftAdvert, OLXAdvert


class OLXAdvertService:
    def __init__(self, db: Session):
        self.db = db
        self.auth = OLXAuth(db)

    def get_advert_description(self, unit: Unit, product: Product) -> str:
        parts = []

        # 1. Advert Title
        parts.append(product.title or "")
        if unit.title_suffix:
            parts[0] += f" {unit.title_suffix}"

        # 2. Product description
        if product.description:
            parts.append(product.description.strip())

        # 3. Internal reference
        parts.append(f"Ref. Interna: {product.sku}-{unit.sku}")

        # 4. Alternative references
        if unit.alternative_sku:
            parts.append(f"Ref. Alternativa(s): {unit.alternative_sku}")

        # 5. Kilometers
        if unit.km:
            parts.append(f"Kilómetros: {unit.km:,}.000")

        # 6. Observations
        if unit.observations:
            parts.append(unit.observations.strip())

        if unit.product.component_ref in ("KF", "KB"):  # motor or gearbox
            parts.append("\nGarantia de produto: 3 meses")

        # 7. Compatible models
        compat_models = (
            self.db.query(ProductCompatibility)
            .filter(ProductCompatibility.product_id == product.id)
            .all()
        )
        if compat_models:
            lines = ["\nCompatibilidades (alguns exemplos):"]
            for cm in compat_models:
                m: Model = self.db.query(Model).get(cm.model_id)
                if m:
                    lines.append(f"{m.make.name} {m.name}")
            parts.append("\n".join(lines))

        # 9. Seller name
        parts.append("\n" + OLX.CONTACT_NAME)

        return "\n".join(parts).strip()

    async def process_draft_to_olx(self, draft: OLXDraftAdvert) -> dict:
        """
        Process a single draft: send to OLX and update database.
        Returns result dict with success/error info.
        """
        try:
            unit = self.db.query(Unit).filter(Unit.id == draft.unit_id).first()
            if not unit:
                return {"draft_id": draft.id, "error": "Unit not found"}

            product = self.db.query(Product).filter(
                Product.id == unit.product_id).first()
            if not product:
                return {"draft_id": draft.id, "error": "Product not found"}

            # Build and send to OLX
            payload = self._build_advert_payload(unit, product)
            olx_result = await self._send_advert(payload)

            # Extract OLX advert ID
            olx_advert_id = olx_result.get("data", {}).get(
                "id") or olx_result.get("id")

            if olx_advert_id:
                return self._move_draft_to_advert(draft, unit.id, olx_advert_id)
            else:
                self._save_draft_error(draft, "No advert ID in OLX response")
                return {"draft_id": draft.id, "error": "No advert ID in OLX response"}

        except Exception as e:
            self._save_draft_error(draft, str(e))
            return {"draft_id": draft.id, "error": str(e)}

    def _move_draft_to_advert(self, draft: OLXDraftAdvert,
                              unit_id: int,
                              olx_advert_id: str) -> dict:
        """Move successful draft to olx_adverts table."""
        try:
            from app.model.olx import OLXAdvert

            olx_advert = OLXAdvert(
                unit_id=unit_id,
                olx_advert_id=str(olx_advert_id),
                status="limited"
            )
            self.db.add(olx_advert)
            self.db.delete(draft)
            self.db.commit()

            self._cleanup_temp_photos(unit_id)

            return {
                "draft_id": draft.id,
                "success": True,
                "olx_id": olx_advert_id
            }
        except Exception as e:
            self.db.rollback()
            return {"draft_id": draft.id, "error": f"Database error: {str(e)}"}

    def _save_draft_error(self, draft: OLXDraftAdvert, error_msg: str):
        """Save error message in draft for later retry."""
        try:
            draft.error = error_msg
            self.db.commit()
        except:
            self.db.rollback()

    async def _send_advert(self, payload: dict) -> dict:
        token = self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Version": "2.0",
            "Accept": "application/json",
            "User-Agent": "PartStock/1.0",
        }
        url = OLX.ADVERTS_URL

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            raise Exception(f"OLX error {resp.status_code}: {resp.text}")

        return resp.json()

    def _build_advert_payload(self, unit, product) -> dict:
        """
        Build OLX advert payload for a given unit + product.
        For now: includes only 1 static test image.
        """
        price_value = OLX.calc_price(unit.selling_price)

        unit_photos = self.db.query(UnitPhoto).filter(
            UnitPhoto.unit_id == unit.id).all()
        cloudflare_url = settings.get_cloudflare_url()

        images = []
        for photo in unit_photos:
            images.append({"url": f"{cloudflare_url}/{photo.filename}"})

        return {
            "title": f"{product.title} {unit.title_suffix or ''}".strip(),
            "description": self.get_advert_description(unit, product),
            "category_id": OLX.CATEGORY_ID,
            "advertiser_type": OLX.ADVERTISER_TYPE,
            "contact": {
                "name": OLX.CONTACT_NAME,
                "phone": OLX.CONTACT_PHONE
            },
            "location": {"city_id": OLX.CITY_ID},
            "price": {
                "value": price_value,
                "currency": OLX.CURRENCY,
                "negotiable": False,
                "trade": False,
                "budget": False
            },
            "attributes": OLX.ATTRIBUTES,
            "images": images
        }

    def _cleanup_temp_photos(self, unit_id: int):
        """Delete temporary photos for a specific unit after successful advert creation."""
        try:
            from pathlib import Path

            # Get all photos for this unit
            unit_photos = self.db.query(UnitPhoto).filter(
                UnitPhoto.unit_id == unit_id
            ).all()

            temp_dir = Path(settings.TEMP_PHOTO_DIR)
            deleted_count = 0

            for photo in unit_photos:
                temp_file_path = temp_dir / photo.filename
                if temp_file_path.exists():
                    try:
                        temp_file_path.unlink()  # Delete the file
                        deleted_count += 1
                    except OSError as e:
                        # Log but don't fail - temp cleanup is not critical
                        print(f"Warning: Could not delete temp photo {
                              photo.filename}: {e}")

            print(f"Cleaned up {
                  deleted_count} temporary photos for unit {unit_id}")

        except Exception as e:
            # Don't fail the whole operation if temp cleanup fails
            print(f"Warning: Temp photo cleanup failed for unit {
                  unit_id}: {e}")
