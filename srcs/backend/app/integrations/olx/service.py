import httpx
from app.models import Unit, Product, ProductCompatibility, Model
from app.integrations.olx.constants import OLX
from sqlalchemy.orm import Session
from app.integrations.olx.auth import OLXAuth


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
            parts.append(f"Km: {unit.km:,} km")

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

    async def send_advert(self, payload: dict) -> dict:
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

        if resp.status_code != 201:
            raise Exception(f"OLX error {resp.status_code}: {resp.text}")

        return resp.json()

    def build_advert_payload(self, unit, product) -> dict:
        """
        Build OLX advert payload for a given unit + product.
        For now: includes only 1 static test image.
        """
        price_value = OLX.calc_price(unit.selling_price)

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
            "images": [
                {
                    "url": "https://media.adeo.com/mkp/ba532be921b42dc5f1aea7ea203229fc/media.png?width=3000&height=3000&format=jpg&quality=80&fit=bounds"
                }
            ]
        }
