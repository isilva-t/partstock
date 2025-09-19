# app/integrations/olx/service.py

from app.models import Unit, Product, ProductCompatibility, Model
from app.integrations.olx.constants import OLX
from sqlalchemy.orm import Session


class OLXAdvertService:
    def __init__(self, db: Session):
        self.db = db

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
