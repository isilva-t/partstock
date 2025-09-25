from app.database import engine
from app.models import Product, Unit, ProductCompatibility, ProductPhoto
from app.model import olx  # noqa: F401 - Import to register OLX models
from app.config import settings
import pandas as pd
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import re
import shutil
import datetime


def is_valid_id(value):
    """Check if a value is a valid numeric ID"""
    try:
        if pd.isna(value) or str(value).strip() == '':
            return False
        # Handle both int and float values from pandas
        numeric_value = float(str(value).strip())
        # Check if it's a valid positive integer (even if stored as float)
        return numeric_value > 0 and numeric_value == int(numeric_value)
    except (ValueError, TypeError):
        return False


def extract_photo_base_info(photo_filename):
    """Extract base name and sequence from photo filename
    Example: '050_1.jpg' -> ('050', 1)
    """
    if not photo_filename:
        return None, None

    try:
        # Remove .jpg extension and split by underscore
        name_without_ext = photo_filename.replace(
            '.jpg', '').replace('.JPG', '')
        parts = name_without_ext.split('_')

        if len(parts) >= 2:
            base_name = parts[0]
            sequence = int(parts[1])
            return base_name, sequence
    except (ValueError, IndexError):
        pass

    return None, None


def find_photo_variants(base_name, temp_photos_dir):
    """Find all photo variants for a base name
    Example: base_name='050' -> look for 050_1.jpg, 050_2.jpg, 050_3.jpg
    """
    variants = []

    for i in range(1, 4):  # Check _1, _2, _3
        photo_filename = f"{base_name}_{i}.jpg"
        photo_path = temp_photos_dir / photo_filename

        if photo_path.exists():
            variants.append(photo_filename)
        else:
            # Also try uppercase extension
            photo_filename_upper = f"{base_name}_{i}.JPG"
            photo_path_upper = temp_photos_dir / photo_filename_upper
            if photo_path_upper.exists():
                variants.append(photo_filename_upper)

    return variants


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

            products_loaded = 0
            products_skipped = 0

            for _, row in df_products.iterrows():
                # Skip rows without valid ID
                if not is_valid_id(row['id']):
                    products_skipped += 1
                    print(f"⚠️  Skipping row with invalid ID: {
                          row.get('id', 'N/A')}")
                    continue

                # Generate SKU by concatenating component_ref + sku_id
                sku = row['component_ref'] + str(int(row['sku_id']))

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
                products_loaded += 1

            print(f"✅ Product examples loaded: {products_loaded}")
            print(f"⚠️  Products skipped (invalid ID): {products_skipped}")

            # Commit products first
            session.commit()

            # Now populate product photos
            print("\n📸 Processing product photos...")
            populate_product_photos(session, df_products)

        else:
            print("⚠️ Product example CSV not found, skipping")

        session.commit()
        print("🎉 All example data loaded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error loading example data: {e}")
        raise
    finally:
        session.close()


def populate_product_photos(session, df_products):
    """Populate product photos from temp_photos directory"""
    import shutil
    import time
    import datetime

    temp_photos_dir = Path("data/temp_photos")

    # Create product photo directory if it doesn't exist
    photo_dir = Path(settings.PRODUCT_PHOTO_DIR)
    photo_dir.mkdir(parents=True, exist_ok=True)

    if not temp_photos_dir.exists():
        print(f"⚠️  Temp photos directory not found: {temp_photos_dir}")
        return

    photos_created = 0
    products_with_photos = 0

    for _, row in df_products.iterrows():
        # Skip rows without valid ID (same validation as products)
        if not is_valid_id(row['id']) or pd.isna(row.get('photo_filename')):
            continue

        # Get the actual product to get its SKU
        product = session.query(Product).filter(
            Product.id == row['id']).first()
        if not product:
            print(f"⚠️  Product not found for ID: {row['id']}")
            continue

        photo_filename = str(row['photo_filename']).strip()
        if not photo_filename:
            continue

        component_ref = str(row['component_ref']).strip()
        if not component_ref:
            continue

        sku = str(row['sku']).strip()
        if not sku:
            continue

        # Extract base info from the photo filename
        base_name, sequence = extract_photo_base_info(photo_filename)
        if not base_name:
            print(f"⚠️  Could not parse photo filename: {photo_filename}")
            continue

        # Find all photo variants for this base name
        photo_variants = find_photo_variants(base_name, temp_photos_dir)

        if photo_variants:
            products_with_photos += 1
            print(f"📸 Found {len(photo_variants)} photos for product ID {
                  row['id']} (SKU: {product.sku}): {photo_variants}")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            for variant_filename in photo_variants:
                # Extract sequence from the original filename
                base_name, sequence = extract_photo_base_info(variant_filename)

                # Generate unique timestamp for each photo
                new_filename = f"{product.sku}_{sequence}_{timestamp}.jpg"

                # Check if this photo record already exists
                existing_photo = session.query(ProductPhoto).filter(
                    ProductPhoto.product_id == product.id,
                    ProductPhoto.filename == new_filename
                ).first()

                if not existing_photo:
                    # Copy file from temp to products directory
                    source_path = temp_photos_dir / variant_filename
                    dest_path = photo_dir / component_ref / sku / new_filename
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(source_path, dest_path)
                        print(f"  📁 Copied: {
                              variant_filename} → {new_filename}")

                        # Save to database with new filename
                        photo_record = ProductPhoto(
                            product_id=product.id,
                            filename=new_filename
                        )
                        session.add(photo_record)
                        photos_created += 1

                    except Exception as e:
                        print(f"  ❌ Error copying {variant_filename}: {e}")
                else:
                    print(f"  ⚠️  Photo already exists: {new_filename}")

                # Small delay to ensure unique timestamps
                time.sleep(0.01)

    print(f"✅ Product photos processed:")
    print(f"   - Products with photos: {products_with_photos}")
    print(f"   - New photo records created: {photos_created}")


def clear_example_data():
    """Clear all example data (useful for development)"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Clearing existing example data...")

        # Delete in correct order due to foreign key constraints
        session.query(ProductPhoto).delete()
        session.query(ProductCompatibility).delete()
        session.query(Unit).delete()
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
