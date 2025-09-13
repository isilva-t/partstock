from app.database import engine
from app.models import Product, Instance, ProductCompatibility
from app.config import settings
import pandas as pd
from sqlalchemy.orm import sessionmaker


def load_example_data():
    """Load example data from CSV files"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Load Products
        if settings.product_example_csv_path:
            print("Loading product examples...")
            df_products = pd.read_csv(
                settings.product_example_csv_path, sep=';')

            for _, row in df_products.iterrows():
                # Generate SKU by concatenating component_ref + sku_id
                sku = row['component_ref'] + str(row['sku_id'])

                product = Product(
                    id=row['id'],
                    component_ref=row['component_ref'],
                    sku_id=row['sku_id'],
                    sku=sku,
                    title=row['title'],
                    description=row['description'],
                    reference_price=row['reference_price']
                )
                session.merge(product)
            print("✅ Product examples loaded")
        else:
            print("⚠️ Product example CSV not found, skipping")

        # Load Product Compatibility
        if settings.product_compatibility_csv_path:
            print("Loading product compatibility...")
            df_compatibility = pd.read_csv(
                settings.product_compatibility_csv_path, sep=';')

            for _, row in df_compatibility.iterrows():
                compatibility = ProductCompatibility(
                    id=row['id'],
                    product_id=row['product_id'],
                    model_id=row['model_id']
                )
                session.merge(compatibility)
            print("✅ Product compatibility loaded")
        else:
            print("⚠️ Product compatibility CSV not found, skipping")

        # Load Instances
        if settings.instance_example_csv_path:
            print("Loading instance examples...")
            df_instances = pd.read_csv(
                settings.instance_example_csv_path, sep=';')

            for _, row in df_instances.iterrows():
                # Generate SKU by concatenating year_month + sku_id
                sku = row['year_month'] + str(row['sku_id'])

                instance = Instance(
                    id=row['id'],
                    product_id=row['product_id'],
                    year_month=row['year_month'],
                    sku_id=row['sku_id'],
                    sku=sku,
                    alternative_sku=row.get('alternative_sku'),
                    selling_price=row['selling_price'],
                    km=row.get('KM') if pd.notna(row.get('KM')) else None,
                    observations=row.get('observations'),
                    status=row.get('status', 'active')
                )
                session.merge(instance)
            print("✅ Instance examples loaded")
        else:
            print("⚠️ Instance example CSV not found, skipping")

        session.commit()
        print("🎉 All example data loaded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error loading example data: {e}")
        raise
    finally:
        session.close()


def clear_example_data():
    """Clear all example data (useful for development)"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Clearing existing example data...")

        # Delete in correct order due to foreign key constraints
        session.query(ProductCompatibility).delete()
        session.query(Instance).delete()
        session.query(Product).delete()

        session.commit()
        print("✅ Example data cleared")

    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_example_data()
    else:
        load_example_data()
