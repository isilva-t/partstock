import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.database import engine, Base
from app.models import Make, Model
from app.config import settings
from app.model import olx  # noqa: F401


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def load_makes_and_models():
    """Load only makes and models from CSV"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        if settings.make_csv_path:
            df_makes = pd.read_csv(settings.make_csv_path, sep=';')
            for _, row in df_makes.iterrows():
                session.merge(Make(id=row['id'], name=row['name']))
            print("✅ Makes loaded")
        else:
            print("⚠️ Make CSV not found, skipping")

        if settings.model_csv_path:
            df_models = pd.read_csv(settings.model_csv_path, sep=';')
            for _, row in df_models.iterrows():
                session.merge(Model(
                    id=row['id'],
                    make_id=row['make_id'],
                    name=row['name'],
                    start_year=row['start_year'],
                    end_year=row['end_year']
                ))
            print("✅ Models loaded")
        else:
            print("⚠️ Model CSV not found, skipping")

        session.commit()
        print("🎉 Makes & Models loaded successfully!")
    except Exception as e:
        session.rollback()
        print(f"❌ Error loading makes/models: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_tables()
    load_makes_and_models()
