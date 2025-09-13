import datetime


class Tools:
    @staticmethod
    def get_cur_year_month() -> str:
        """
        Generate year_month code based on current date.
        Format: YY + Letter (A=Jan, B=Feb, ..., L=Dec)
        Example: "25A" for January 2025, "25L" for December 2025
        """
        now = datetime.datetime.now()

        # Get last 2 digits of year
        year_suffix = str(now.year)[-2:]
        # Convert month (1-12) to letter (A-L)
        month_letter = chr(ord('A') + now.month - 1)

        return year_suffix + month_letter
