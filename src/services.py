import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def get_analize_cashback(filepath: str, year: int, month: int) -> str:
    """
    Функция анализирует выгодные категории кешбека
    и возвращает json
    """
    try:
        logger.info(f"Анализ кэшбэка за {month}.{year}")

        df = pd.read_excel(filepath)
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        filt_data = df[(df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)]
        filt_data = filt_data[filt_data["Кэшбэк"].notna()]
        filt_data = filt_data[filt_data["Сумма платежа"] < 0]

        cashback_category = filt_data.groupby("Категория")["Кэшбэк"].sum()
        sort_cashback_category = cashback_category.sort_values(ascending=False)

        result = {"year": year, "month": month, "cashback_categories": sort_cashback_category.to_dict()}
        logger.info("Анализ для get_analize_cashback завершен")
        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"Ошибка в анализе кэшбэка {e}")
        return json.dumps({"error": "cachback_error"}, ensure_ascii=False, indent=4)
