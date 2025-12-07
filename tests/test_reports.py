import logging
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
from _pytest.logging import LogCaptureFixture

from src.reports import spending_by_category


def create_sample_transactions() -> pd.DataFrame:
    """Тестовые данные"""
    return pd.DataFrame(
        {
            "Дата операции": ["01.03.2024", "15.03.2024", "01.04.2024", "20.04.2024", "01.05.2024", "25.05.2024"],
            "Сумма операции": [-1000, -500, -2000, -300, -1500, -800],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты", "Рестораны", "Супермаркеты", "Аптека"],
            "Описание": ["Покупка", "Такси", "Продукты", "Ужин", "Продукты", "Лекарства"],
        }
    )


def test_spending_by_category_success_default_date(caplog: LogCaptureFixture) -> None:
    """Тест: траты по категории за последние 3 месяца от текущей даты (1 июня 2024)"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    with patch("src.reports.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 6, 1)
        mock_datetime.strptime = datetime.strptime
        mock_datetime.timedelta = timedelta
        mock_datetime.datetime = datetime

        result = spending_by_category(sample_transactions, "Супермаркеты")

    assert len(result) == 2
    assert set(result["Сумма операции"]) == {-2000, -1500}
    assert list(result.columns) == ["Дата операции", "Сумма операции", "Описание"]
    assert "Найдено 2 транзакций по категории: Супермаркеты" in caplog.text


def test_spending_by_category_with_custom_date(caplog: LogCaptureFixture) -> None:
    """Тест: траты по категории с указанной датой (1 мая 2024)"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    result = spending_by_category(sample_transactions, "Супермаркеты", date="2024-05-01")

    assert len(result) == 3
    assert set(result["Сумма операции"]) == {-1000, -2000, -1500}


def test_spending_by_category_filters_income(caplog: LogCaptureFixture) -> None:
    """Тест: доходы (положительные суммы) не учитываются"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    df_with_income = sample_transactions.copy()
    df_with_income.loc[len(df_with_income)] = {
        "Дата операции": "10.05.2024",
        "Сумма операции": 5000,
        "Категория": "Супермаркеты",
        "Описание": "Возврат",
    }

    result = spending_by_category(df_with_income, "Супермаркеты", date="2024-06-01")
    assert len(result) == 2
    assert all(result["Сумма операции"] < 0)
