from app.database import engine, Base
from app.models import Make, Model, Category, SubCategory, Component
from app.config import settings
import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.model import olx  # noqa: F401


def create_tables():
    """create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def load_csv_data():
    """Load data from CSV's"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if settings.make_csv_path:
            df_makes = pd.read_csv(settings.make_csv_path, sep=';')
            for _, row in df_makes.iterrows():
                make = Make(id=row['id'], name=row['name'])
                session.merge(make)
            print("✅ Makes loaded")
        else:
            print("⚠️ Make CSV not found, skipping")

        if settings.model_csv_path:
            df_models = pd.read_csv(settings.model_csv_path, sep=';')
            for _, row in df_models.iterrows():
                model = Model(
                    id=row['id'],
                    make_id=row['make_id'],
                    name=row['name'],
                    start_year=row['start_year'],
                    end_year=row['end_year']
                )
                session.merge(model)
            print("✅ Models loaded")
        else:
            print("⚠️ Model CSV not found, skipping")

        if settings.category_csv_path:
            df_categories = pd.read_csv(settings.category_csv_path, sep=';')
            for _, row in df_categories.iterrows():
                category = Category(id=row['id'], name=row['name'])
                session.merge(category)
            print("✅ Categories loaded")
        else:
            print("⚠️ Category CSV not found, skipping")

        if settings.sub_category_csv_path:
            df_sub_categories = pd.read_csv(
                settings.sub_category_csv_path, sep=';')
            for _, row in df_sub_categories.iterrows():
                sub_category = SubCategory(
                    id=row['id'],
                    category_id=row['category_id'],
                    name=row['name'],
                    ref_example=row['ref_example']
                )
                session.merge(sub_category)
            print("✅ Sub-categories loaded")
        else:
            print("⚠️ Sub-category CSV not found, skipping")

        if settings.component_csv_path:
            df_components = pd.read_csv(settings.component_csv_path, sep=';')
            for _, row in df_components.iterrows():
                component = Component(
                    id=row['id'],
                    sub_category_id=row['sub_category_id'],
                    name=row['name'],
                    ref=row['ref']
                )
                session.merge(component)
            print("✅ Components loaded")
        else:
            print("⚠️ Component CSV not found, skipping")

        session.commit()
        print("✅ CSV data loaded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error loading data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    create_tables()
    load_csv_data()
