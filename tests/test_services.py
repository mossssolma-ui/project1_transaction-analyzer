import json
import logging
from unittest.mock import patch

import pandas as pd
from _pytest.logging import LogCaptureFixture

from src.services import get_analize_cashback


def test_get_analize_cashback_success(caplog: LogCaptureFixture) -> None:
    """Тест успешного анализа кешбэка за указанный месяц и год"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame({
        "Дата операции": ["01.05.2021", "15.05.2021", "10.06.2021", "20.05.2021"],
        "Сумма платежа": [-1000, -500, -2000, -300],
        "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты", "Рестораны"],
        "Кэшбэк": [10.0, 5.0, 20.0, 6.0]
    })

    with patch("pandas.read_excel", return_value=test_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response["year"] == 2021
    assert response["month"] == 5
    assert response["cashback_categories"] == {"Супермаркеты": 10.0, "Транспорт": 5.0, "Рестораны": 6.0}

    assert "Анализ кэшбэка за 5.2021" in caplog.text
    assert "Анализ для get_analize_cashback завершен" in caplog.text


def test_get_analize_cashback_no_data_for_period(caplog: LogCaptureFixture) -> None:
    """Тест: нет транзакций за указанный месяц"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame({
        "Дата операции": ["01.03.2021", "15.03.2021"],
        "Сумма платежа": [-1000, -500],
        "Категория": ["Супермаркеты", "Транспорт"],
        "Кэшбэк": [10.0, 5.0]
    })

    with patch("pandas.read_excel", return_value=test_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response["cashback_categories"] == {}


def test_get_analize_cashback_filters_positive_payments(caplog: LogCaptureFixture) -> None:
    """Тест: учитываются только отрицательные 'Сумма платежа'"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame({
        "Дата операции": ["01.05.2021", "15.05.2021", "20.05.2021"],
        "Сумма платежа": [-1000, 500, -300],
        "Категория": ["Супермаркеты", "Зарплата", "Рестораны"],
        "Кэшбэк": [10.0, 0.0, 6.0]
    })

    with patch("pandas.read_excel", return_value=test_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response["cashback_categories"] == {"Супермаркеты": 10.0, "Рестораны": 6.0}


def test_get_analize_cashback_filters_nan_cashback(caplog: LogCaptureFixture) -> None:
    """Тест: исключаются строки с NaN в 'Кэшбэк'"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame({
        "Дата операции": ["01.05.2021", "15.05.2021", "20.05.2021"],
        "Сумма платежа": [-1000, -500, -300],
        "Категория": ["Супермаркеты", "Транспорт", "Рестораны"],
        "Кэшбэк": [10.0, None, 6.0]
    })

    with patch("pandas.read_excel", return_value=test_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response["cashback_categories"] == {"Супермаркеты": 10.0, "Рестораны": 6.0}


def test_get_analize_cashback_empty_dataframe(caplog: LogCaptureFixture) -> None:
    """Тест: пустой Excel-файл"""
    caplog.set_level(logging.INFO)

    empty_df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория", "Кэшбэк"])

    with patch("pandas.read_excel", return_value=empty_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response["cashback_categories"] == {}


def test_get_analize_cashback_file_not_found(caplog: LogCaptureFixture) -> None:
    """Тест: ошибка при чтении файла (например, файл не найден)"""
    caplog.set_level(logging.ERROR)

    with patch("pandas.read_excel", side_effect=FileNotFoundError("File not found")):
        result = get_analize_cashback("nonexistent.xlsx", year=2021, month=5)

    response = json.loads(result)
    assert response == {"error": "cachback_error"}
    assert "File not found" in caplog.text
    assert "Ошибка в анализе кэшбэка" in caplog.text


def test_get_analize_cashback_invalid_data_types(caplog: LogCaptureFixture) -> None:
    """Тест: некорректные данные в Excel (например, текст вместо числа в 'Кэшбэк')"""
    caplog.set_level(logging.ERROR)

    bad_df = pd.DataFrame({
        "Дата операции": ["01.05.2021"],
        "Сумма платежа": [-1000],
        "Категория": ["Супермаркеты"],
        "Кэшбэк": ["invalid"]  # строка вместо числа
    })

    with patch("pandas.read_excel", return_value=bad_df):
        result = get_analize_cashback("bad_data.xlsx", year=2021, month=5)

    response = json.loads(result)

    assert isinstance(response, dict)
    assert "error" in response or "cashback_categories" in response


def test_get_analize_cashback_sorting(caplog: LogCaptureFixture) -> None:
    """Тест: категории отсортированы по убыванию кешбэка"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame({
        "Дата операции": ["01.05.2021", "15.05.2021", "20.05.2021", "25.05.2021"],
        "Сумма платежа": [-1000, -500, -2000, -300],
        "Категория": ["Аптека", "Транспорт", "Супермаркеты", "Рестораны"],
        "Кэшбэк": [5.0, 50.0, 30.0, 10.0]
    })

    with patch("pandas.read_excel", return_value=test_df):
        result = get_analize_cashback("dummy_path.xlsx", year=2021, month=5)

    response = json.loads(result)
    categories = list(response["cashback_categories"].keys())
    cashbacks = list(response["cashback_categories"].values())

    assert cashbacks == sorted(cashbacks, reverse=True)
    assert categories[0] == "Транспорт"
