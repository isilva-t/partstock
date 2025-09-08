from app.database import engine, Base
from app.models import Make, Model, Category, SubCategory, Component
import pandas as pd
from sqlalchemy.orm import sessionmaker


def create_tables():
    """create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def load_csv_data():
    """Load data from CSV's"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        df_makes = pd.read_csv('data_to_import/make_table.csv', sep=';')
        for _, row in df_makes.iterrows():
            make = Make(id=row['id'], name=row['name'])
            session.merge(make)

        df_categories = pd.read_csv(
            'data_to_import/category_table.csv', sep=';')
        for _, row in df_categories.iterrows():
            category = Category(id=row['id'], name=row['name'])
            session.merge(category)

        df_sub_categories = pd.read_csv(
            'data_to_import/sub_category_table.csv', sep=';')
        for _, row in df_sub_categories.iterrows():
            sub_category = SubCategory(
                id=row['id'],
                category_id=row['category_id'],
                name=row['name'],
                ref_example=row['ref_example']
            )
            session.merge(sub_category)

        df_components = pd.read_csv(
            'data_to_import/component_table.csv', sep=';')
        for _, row in df_components.iterrows():
            component = Component(
                id=row['id'],
                sub_category_id=row['sub_category_id'],
                name=row['name'],
                ref=row['ref']
            )
            session.merge(component)

        df_models = pd.read_csv('data_to_import/model_table.csv', sep=';')
        for _, row in df_models.iterrows():
            model = Model(
                id=row['id'],
                make_id=row['make_id'],
                name=row['name'],
                start_year=row['start_year'],
                end_year=row['end_year']
            )
            session.merge(model)

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
