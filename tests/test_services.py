import json
import logging
from unittest.mock import patch

import pandas as pd
from _pytest.logging import LogCaptureFixture

from src.services import analyze_cashback_by_category, get_analize_cashback


def create_sample_transactions() -> pd.DataFrame:
    """Вспомогательная функция для создания тестовых данных"""
    return pd.DataFrame(
        {
            "Дата операции": [
                "01.03.2021",
                "15.03.2021",
                "01.04.2021",
                "20.04.2021",
                "01.05.2021",
                "25.05.2021",
                "10.05.2021",
            ],
            "Сумма операции": [-1000, -500, -2000, -300, -1500, -800, 5000],
            "Сумма платежа": [-1000, -500, -2000, -300, -1500, -800, 5000],
            "Категория": [
                "Супермаркеты",
                "Транспорт",
                "Супермаркеты",
                "Рестораны",
                "Супермаркеты",
                "Аптека",
                "Супермаркеты",
            ],
            "Кэшбэк": [10.0, 5.0, 20.0, 6.0, 15.0, 8.0, None],
            "Описание": ["Покупка", "Такси", "Продукты", "Ужин", "Продукты", "Лекарства", "Возврат"],
        }
    )


def test_analyze_cashback_by_category_success(caplog: LogCaptureFixture) -> None:
    """Тест: успешный анализ кешбэка по категориям"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    result = analyze_cashback_by_category(sample_transactions, year=2021, month=5)

    # Проверяем структуру результата
    assert "year" in result
    assert "month" in result
    assert "cashback_categories" in result
    assert result["year"] == 2021
    assert result["month"] == 5

    expected_categories = {"Супермаркеты": 15.0, "Аптека": 8.0}
    assert result["cashback_categories"] == expected_categories

    assert "Анализ кэшбэка за 5.2021" in caplog.text
    assert "Анализ кэшбэка завершен" in caplog.text


def test_analyze_cashback_by_category_no_data_for_period(caplog: LogCaptureFixture) -> None:
    """Тест: нет транзакций за указанный период"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    result = analyze_cashback_by_category(sample_transactions, year=2021, month=6)

    assert result["cashback_categories"] == {}
    assert "Анализ кэшбэка за 6.2021" in caplog.text


def test_analyze_cashback_by_category_filters_income(caplog: LogCaptureFixture) -> None:
    """Тест: доходы (положительные суммы) не учитываются"""
    caplog.set_level(logging.INFO)
    sample_transactions = create_sample_transactions()

    result = analyze_cashback_by_category(sample_transactions, year=2021, month=5)

    assert "Супермаркеты" in result["cashback_categories"]
    assert result["cashback_categories"]["Супермаркеты"] == 15.0


def test_analyze_cashback_by_category_filters_nan_cashback(caplog: LogCaptureFixture) -> None:
    """Тест: транзакции с NaN в кешбэке исключаются"""
    caplog.set_level(logging.INFO)
    test_df = pd.DataFrame(
        {
            "Дата операции": ["01.05.2021", "15.05.2021"],
            "Сумма операции": [-1000, -500],
            "Сумма платежа": [-1000, -500],
            "Категория": ["Супермаркеты", "Транспорт"],
            "Кэшбэк": [10.0, None],
            "Описание": ["Покупка", "Такси"],
        }
    )

    result = analyze_cashback_by_category(test_df, year=2021, month=5)

    assert result["cashback_categories"] == {"Супермаркеты": 10.0}


def test_analyze_cashback_by_category_empty_dataframe(caplog: LogCaptureFixture) -> None:
    """Тест: пустой DataFrame"""
    caplog.set_level(logging.INFO)

    empty_df = pd.DataFrame(
        columns=["Дата операции", "Сумма операции", "Сумма платежа", "Категория", "Кэшбэк", "Описание"]
    )

    result = analyze_cashback_by_category(empty_df, year=2021, month=5)
    assert result["cashback_categories"] == {}


def test_analyze_cashback_by_category_sorting(caplog: LogCaptureFixture) -> None:
    """Тест: категории отсортированы по убыванию кешбэка"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame(
        {
            "Дата операции": ["01.05.2021", "15.05.2021", "20.05.2021"],
            "Сумма операции": [-1000, -500, -2000],
            "Сумма платежа": [-1000, -500, -2000],
            "Категория": ["Аптека", "Транспорт", "Супермаркеты"],
            "Кэшбэк": [5.0, 50.0, 30.0],
            "Описание": ["Лекарства", "Такси", "Продукты"],
        }
    )

    result = analyze_cashback_by_category(test_df, year=2021, month=5)
    categories = list(result["cashback_categories"].keys())

    assert categories == ["Транспорт", "Супермаркеты", "Аптека"]


def test_analyze_cashback_by_category_exception_handling(caplog: LogCaptureFixture) -> None:
    """Тест: обработка исключений в бизнес-логике"""
    caplog.set_level(logging.ERROR)

    bad_df = pd.DataFrame({"invalid_column": [1, 2, 3]})

    result = analyze_cashback_by_category(bad_df, year=2021, month=5)

    assert "error" in result
    assert result["error"] == "cashback_error"
    assert "Ошибка в analyze_cashback_by_category" in caplog.text


def test_get_analize_cashback_success(caplog: LogCaptureFixture) -> None:
    """Тест: успешное чтение файла и анализ"""
    caplog.set_level(logging.INFO)

    test_df = create_sample_transactions()

    with patch("pandas.read_excel", return_value=test_df):
        result_json = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    result = json.loads(result_json)
    assert "cashback_categories" in result
    assert result["year"] == 2021
    assert result["month"] == 5


def test_get_analize_cashback_file_not_found(caplog: LogCaptureFixture) -> None:
    """Тест: ошибка при чтении несуществующего файла"""
    caplog.set_level(logging.ERROR)

    with patch("pandas.read_excel", side_effect=FileNotFoundError("File not found")):
        result_json = get_analize_cashback("nonexistent.xlsx", year=2021, month=5)

    result = json.loads(result_json)
    assert "error" in result
    assert "File not found" in caplog.text


def test_get_analize_cashback_invalid_json_return(caplog: LogCaptureFixture) -> None:
    """Тест: возвращаемый JSON валиден"""
    caplog.set_level(logging.INFO)

    test_df = create_sample_transactions()

    with patch("pandas.read_excel", return_value=test_df):
        result_json = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    result = json.loads(result_json)
    assert isinstance(result, dict)

    assert "year" in result
    assert "month" in result
    assert "cashback_categories" in result
