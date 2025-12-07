import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def analyze_cashback_by_category(transactions: pd.DataFrame, year: int, month: int) -> dict:
    """
    Анализирует выгодные категории кешбэка за указанный месяц и год.
    Принимает DataFrame с транзакциями и возвращает словарь с результатами.
    """
    try:
        logger.info(f"Анализ кэшбэка за {month}.{year}")

        df = transactions.copy()
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        mask = (
            (df["Дата операции"].dt.year == year)
            & (df["Дата операции"].dt.month == month)
            & (df["Кэшбэк"].notna())
            & (df["Сумма платежа"] < 0)
        )
        filtered = df[mask]

        cashback_by_category = filtered.groupby("Категория")["Кэшбэк"].sum()
        sorted_result = cashback_by_category.sort_values(ascending=False).to_dict()

        logger.info("Анализ кэшбэка завершен")
        return {"year": year, "month": month, "cashback_categories": sorted_result}

    except Exception as e:
        logger.error(f"Ошибка в analyze_cashback_by_category: {e}")
        return {"error": "cashback_error"}


def get_analize_cashback(filepath: str, year: int, month: int) -> str:
    """
    Вспомогательная функция для удобства использования.
    Читает данные из файла и вызывает бизнес-логику.
    """
    try:
        df = pd.read_excel(filepath)
        result = analyze_cashback_by_category(df, year, month)
        return json.dumps(result, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filepath}: {e}")
        return json.dumps({"error": "cashback_error"}, ensure_ascii=False, indent=4)
