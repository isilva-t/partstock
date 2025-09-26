import datetime
from datetime import datetime
from decimal import Decimal
import math
from app.config import settings


class Tools:
    @staticmethod
    def get_cur_year_month() -> str:
        """
        Generate year_month code based on current date.
        Format: YY + Letter (A=Jan, B=Feb, ..., L=Dec)
        Example: "25A" for January 2025, "25L" for December 2025
        """
        now = datetime.now()

        # Get last 2 digits of year
        year_suffix = str(now.year)[-2:]
        # Convert month (1-12) to letter (A-L)
        month_letter = chr(ord('A') + now.month - 1)

        return year_suffix + month_letter

    @staticmethod
    def calc_vat_price(selling_price: int) -> int:
        """
        VAT calculation (not rounded).
        - selling_price: int (cents)
        - returns float in euros (e.g. 124.23)
        """
        multiplier = float(settings.VAT_MULTIPLIER)

        with_vat: float = selling_price * multiplier
        return int(with_vat + 0.5)

    @staticmethod
    def calc_vat_price_rounded(selling_price: int) -> int:
        """
        VAT calculation (rounded up).
        - selling_price: int (cents)
        - returns int in euros (e.g. 125)
        """

        euro_price = Decimal(Tools.calc_vat_price(selling_price) / 100)
        with_vat_rounded = math.ceil(euro_price)
        return with_vat_rounded

    @staticmethod
    def format_dt(dt_str):
        return (
            datetime.strptime(
                dt_str, "%Y-%m-%d %H:%M:%S").strftime("%d-%m %H:%M")
            if dt_str else None
        )
