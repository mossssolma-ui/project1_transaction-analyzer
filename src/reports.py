import functools
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import pandas as pd

loger = logging.getLogger(__name__)


def report_decorator(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для записи отчетов в файл.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                loger.info(f"Запуск отчета: {func.__name__}")
                result = func(*args, **kwargs)

                if filename is None:
                    report_filename = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                else:
                    report_filename = filename

                with open(f"logs/{report_filename}", "w", encoding="utf-8") as f:
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

                loger.info(f"Отчет сохранен в файл: {report_filename}")
                return result
            except Exception as e:
                loger.error(f"Ошибка в декораторе отчета {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Траты по категории за последние 3 месяца
    """
    try:
        loger.info(f"Анализ трат по категории {category} за последнии 3 месяца")

        df = transactions.copy()

        if isinstance(df["Дата операции"].iloc[0], str):
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
            loger.info("Дата операции сконрветирована в datetime")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            loger.info(f"Дата не указана, исп. текущую дату {date}")

        end_date = pd.to_datetime(date)
        start_date = end_date - timedelta(days=90)

        loger.info("Анализ за период")
        filtered = df[
            (df["Дата операции"] >= start_date)
            & (df["Дата операции"] <= end_date)
            & (df["Категория"] == category)
            & (df["Сумма операции"] < 0)
        ]

        loger.info(f"Найдено {len(filtered)} транзакций по категории: {category}")
        return filtered[["Дата операции", "Сумма операции", "Описание"]]

    except Exception as e:
        loger.error(f"Ошибка в spending_by_category: {e}")
        return pd.DataFrame()
