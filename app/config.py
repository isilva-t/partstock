import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # Database - required
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

        # CSV Data Directory - required
        self.CSV_DATA_DIR = os.getenv("CSV_DATA_DIR")
        if not self.CSV_DATA_DIR:
            raise ValueError("CSV_DATA_DIR environment variable is required")

        # Photo Storage
        self.PHOTO_STORAGE_DIR = os.getenv("PHOTO_STORAGE_DIR", "photos")
        self.PRODUCT_PHOTO_DIR = os.getenv(
            "PRODUCT_PHOTO_DIR", "photos/products")
        self.INSTANCE_PHOTO_DIR = os.getenv(
            "INSTANCE_PHOTO_DIR", "photos/instances")

        # App Settings
        self.APP_NAME = os.getenv("APP_NAME", "PartStock Auto Parts Inventory")
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

    def get_existing_csv_path(self, env_var_name):
        """Get CSV path if file exists, None otherwise"""
        filename = os.getenv(env_var_name)
        if not filename:
            return None

        full_path = os.path.join(self.CSV_DATA_DIR, filename)
        return full_path if os.path.exists(full_path) else None

    @property
    def make_csv_path(self):
        return self.get_existing_csv_path("MAKE_TABLE_CSV")

    @property
    def model_csv_path(self):
        return self.get_existing_csv_path("MODEL_TABLE_CSV")

    @property
    def category_csv_path(self):
        return self.get_existing_csv_path("CATEGORY_TABLE_CSV")

    @property
    def sub_category_csv_path(self):
        return self.get_existing_csv_path("SUB_CATEGORY_TABLE_CSV")

    @property
    def component_csv_path(self):
        return self.get_existing_csv_path("COMPONENT_TABLE_CSV")


settings = Settings()
