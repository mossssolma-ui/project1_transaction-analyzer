import json

import pandas as pd


def get_analize_cashback(filepath: str, year: int, month: int) -> str:
    """
    Функция анализирует выгодные категории кешбека
    и возвращает json
    """
    df = pd.read_excel(filepath)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    filt_data = df[(df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)]
    filt_data = filt_data[filt_data["Кэшбэк"].notna()]
    filt_data = filt_data[filt_data["Сумма платежа"] < 0]

    cashback_category = filt_data.groupby("Категория")["Кэшбэк"].sum()
    sort_cashback_category = cashback_category.sort_values(ascending=False)

    result = {"year": year, "month": month, "cashback_categories": sort_cashback_category.to_dict()}
    return json.dumps(result, ensure_ascii=False, indent=4)
