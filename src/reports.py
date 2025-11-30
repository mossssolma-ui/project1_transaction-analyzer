import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Callable
import functools


def report_decorator(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для записи отчетов в файл.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            if filename is None:
                report_filename = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                report_filename = filename

            with open(report_filename, "w", encoding="utf-8") as f:
                if isinstance(result, pd.DataFrame):
                    records = []
                    for _, row in result.iterrows():
                        record = {}
                        for col, value in row.items():
                            if isinstance(value, pd.Timestamp):
                                record[col] = value.strftime("%Y-%m-%d")
                            else:
                                record[col] = value
                        records.append(record)
                    json.dump(records, f, ensure_ascii=False, indent=4)
                else:
                    json.dump(result, f, ensure_ascii=False, indent=4)

            print(f"Отчет сохранен в файл: {report_filename}")
            return result

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Траты по категории за последние 3 месяца
    """
    df = transactions.copy()

    if isinstance(df["Дата операции"].iloc[0], str):
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    end_date = pd.to_datetime(date)
    start_date = end_date - timedelta(days=90)

    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= end_date)
        & (df["Категория"] == category)
        & (df["Сумма операции"] < 0)
    ]

    return filtered[["Дата операции", "Сумма операции", "Описание"]]
