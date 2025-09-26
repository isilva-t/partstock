from app.database import engine
from app.models import Product, Unit, UnitPhoto
from app.model import olx  # noqa: F401 - Import to register OLX models
from app.config import settings
import pandas as pd
from sqlalchemy.orm import sessionmaker
from pathlib import Path
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

    for i in range(1, 10):  # Check _1 to _9 (max 9 photos per unit)
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
        # Load Units
        if settings.unit_example_csv_path:
            print("Loading unit examples...")
            df_units = pd.read_csv(settings.unit_example_csv_path, sep=';')

            units_loaded = 0
            units_skipped = 0

            for _, row in df_units.iterrows():
                # Skip rows without valid ID
                if not is_valid_id(row['id']):
                    units_skipped += 1
                    print(f"⚠️  Skipping row with invalid ID: {
                          row.get('id', 'N/A')}")
                    continue

                # Validate product_id exists
                if not is_valid_id(row['product_id']):
                    units_skipped += 1
                    print(f"⚠️  Skipping row with invalid product_id: {
                          row.get('product_id', 'N/A')}")
                    continue

                # Check if product exists in database
                product_exists = session.query(Product).filter(
                    Product.id == row['product_id']
                ).first()

                if not product_exists:
                    units_skipped += 1
                    print(
                        f"⚠️  Skipping unit - product_id {row['product_id']} not found in database")
                    continue

                # Handle status conversion: "1" -> "limited", else -> "active"
                status_value = str(row.get('status', '')).strip()
                unit_status = "limited" if status_value == "1" else "active"

                # Read SKU as-is from CSV (don't convert to int to avoid .0)
                sku_value = str(row['sku']).strip()

                unit = Unit(
                    id=row['id'],
                    product_id=row['product_id'],
                    year_month=row['year_month'],
                    sku_id=row['sku_id'],
                    sku=sku_value,
                    status=unit_status,
                    title_suffix=row.get('title_suffix'),
                    km=row.get('km'),
                    selling_price=row['selling_price'],
                    created_at=pd.to_datetime(row['created_at']) if pd.notna(
                        row.get('created_at')) else None,
                    updated_at=pd.to_datetime(row['updated_at']) if pd.notna(
                        row.get('updated_at')) else None
                )
                session.merge(unit)
                units_loaded += 1

            print(f"✅ Unit examples loaded: {units_loaded}")
            print(f"⚠️  Units skipped (invalid data): {units_skipped}")

            # Commit units first
            session.commit()

            # Now populate unit photos
            print("\n📸 Processing unit photos...")
            populate_unit_photos(session, df_units)

        else:
            print("⚠️ Unit example CSV not found, skipping")

        session.commit()
        print("🎉 All unit example data loaded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error loading unit example data: {e}")
        raise
    finally:
        session.close()


def populate_unit_photos(session, df_units):
    """Populate unit photos from temp_photos directory"""
    import time

    temp_photos_dir = Path("data/start_photos")

    # Create unit photo directory if it doesn't exist
    photo_dir = Path(settings.UNIT_PHOTO_DIR)
    photo_dir.mkdir(parents=True, exist_ok=True)

    if not temp_photos_dir.exists():
        print(f"⚠️  Start photos directory not found: {temp_photos_dir}")
        return

    photos_created = 0
    units_with_photos = 0

    for _, row in df_units.iterrows():
        # Skip rows without valid ID or photo filename
        if not is_valid_id(row['id']) or pd.isna(row.get('photo_filename')):
            continue

        # Get the actual unit and its product
        unit = session.query(Unit).filter(Unit.id == row['id']).first()
        if not unit:
            print(f"⚠️  Unit not found for ID: {row['id']}")
            continue

        product = session.query(Product).filter(
            Product.id == unit.product_id).first()
        if not product:
            print(f"⚠️  Product not found for unit ID: {row['id']}")
            continue

        photo_filename = str(row['photo_filename']).strip()
        if not photo_filename:
            continue

        # Extract base info from the photo filename
        base_name, sequence = extract_photo_base_info(photo_filename)
        if not base_name:
            print(f"⚠️  Could not parse photo filename: {photo_filename}")
            continue

        # Find all photo variants for this base name
        photo_variants = find_photo_variants(base_name, temp_photos_dir)

        if photo_variants:
            units_with_photos += 1
            print(f"📸 Found {len(photo_variants)} photos for unit ID {
                  row['id']} (SKU: {unit.sku}): {photo_variants}")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            for variant_filename in photo_variants:
                # Extract sequence from the original filename
                base_name, sequence = extract_photo_base_info(variant_filename)

                # Generate filename: {UNIT_SKU}_{PRODUCT_SKU}_{SEQUENCE}_{TIMESTAMP}.jpg
                new_filename = f"{unit.sku}_{product.sku}_{
                    sequence}_{timestamp}.jpg"

                # Check if this photo record already exists
                existing_photo = session.query(UnitPhoto).filter(
                    UnitPhoto.unit_id == unit.id,
                    UnitPhoto.filename == new_filename
                ).first()

                if not existing_photo:
                    # Copy file from temp to units directory
                    # Storage: UNIT_PHOTO_DIR/component_ref/product_sku/filename
                    source_path = temp_photos_dir / variant_filename
                    dest_path = photo_dir / product.component_ref / product.sku / new_filename
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        shutil.copy2(source_path, dest_path)
                        print(f"  📁 Copied: {
                              variant_filename} → {new_filename}")

                        # Save to database with new filename
                        photo_record = UnitPhoto(
                            unit_id=unit.id,
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

    print(f"✅ Unit photos processed:")
    print(f"   - Units with photos: {units_with_photos}")
    print(f"   - New photo records created: {photos_created}")


def clear_example_data():
    """Clear all unit example data (useful for development)"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Clearing existing unit example data...")

        # Delete in correct order due to foreign key constraints
        session.query(UnitPhoto).delete()
        session.query(Unit).delete()

        session.commit()
        print("✅ Unit example data cleared")

    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing unit data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_example_data()
    else:
        load_example_data()
